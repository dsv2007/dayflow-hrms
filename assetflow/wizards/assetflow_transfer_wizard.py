# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions

class AssetFlowTransferWizard(models.TransientModel):
    _name = 'assetflow.transfer.wizard'
    _description = 'Request Asset Transfer'

    asset_id = fields.Many2one('assetflow.asset', string='Asset to Transfer', required=True)
    current_employee_id = fields.Many2one('hr.employee', string='Current Holder', readonly=True)
    new_employee_id = fields.Many2one('hr.employee', string='New Recipient Employee')
    new_department_id = fields.Many2one('hr.department', string='New Recipient Department')
    notes = fields.Text(string='Reason for Transfer', required=True)

    @api.model
    def default_get(self, fields_list):
        res = super(AssetFlowTransferWizard, self).default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id and self.env.context.get('active_model') == 'assetflow.asset':
            asset = self.env['assetflow.asset'].browse(active_id)
            res['asset_id'] = asset.id
            res['current_employee_id'] = asset.employee_id.id
        return res

    def action_apply_transfer(self):
        """Implements the Transfer Workflow: returns active allocation and registers new allocation."""
        self.ensure_one()
        if not self.new_employee_id and not self.new_department_id:
            raise exceptions.ValidationError("Please specify a new Recipient Employee or Department.")

        # 1. Close current active allocation
        active_allocations = self.env['assetflow.allocation'].search([
            ('asset_id', '=', self.asset_id.id),
            ('state', 'in', ['approved', 'active', 'overdue'])
        ])
        for alloc in active_allocations:
            alloc.write({
                'state': 'returned',
                'date_returned': fields.Date.context_today(self),
                'return_condition_notes': f"Transferred via Request: {self.notes}"
            })

        # 2. Register the new allocation
        new_alloc = self.env['assetflow.allocation'].create({
            'asset_id': self.asset_id.id,
            'employee_id': self.new_employee_id.id if self.new_employee_id else False,
            'department_id': self.new_department_id.id if self.new_department_id else False,
            'state': 'requested',
            'notes': self.notes
        })
        
        # Log event in global audit log
        self.env['assetflow.log'].create({
            'asset_id': self.asset_id.id,
            'action': 'transfer',
            'description': f"Transfer initiated from {self.current_employee_id.name or 'N/A'} to {self.new_employee_id.name or self.new_department_id.name}."
        })

        # Send notification to new owner
        self.env['assetflow.notification'].create({
            'name': 'Asset Transfer Request',
            'description': f"Transfer request created for asset {self.asset_id.asset_tag} to you.",
            'user_id': self.new_employee_id.user_id.id or self.env.user.id,
            'state': 'unread'
        })
        
        # If user is Asset Manager or Department Head, auto-approve for speed of demo
        emp_role = self.env.user.employee_id.assetflow_role
        if emp_role in ['manager', 'admin', 'dept_head']:
            new_alloc.action_approve()
            new_alloc.action_activate()

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

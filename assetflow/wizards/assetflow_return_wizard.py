# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AssetFlowReturnWizard(models.TransientModel):
    _name = 'assetflow.return.wizard'
    _description = 'Process Asset Return'

    asset_id = fields.Many2one('assetflow.asset', string='Asset to Return', required=True)
    verified_condition = fields.Selection([
        ('new', 'Brand New'),
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor')
    ], string='Verified Return Condition', default='good', required=True)
    check_in_notes = fields.Text(string='Condition / Return Notes', required=True)

    @api.model
    def default_get(self, fields_list):
        res = super(AssetFlowReturnWizard, self).default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id and self.env.context.get('active_model') == 'assetflow.asset':
            res['asset_id'] = active_id
        return res

    def action_apply_return(self):
        """Closes allocation, writes log details, and updates the condition on the asset."""
        self.ensure_one()
        active_allocations = self.env['assetflow.allocation'].search([
            ('asset_id', '=', self.asset_id.id),
            ('state', 'in', ['approved', 'active', 'overdue'])
        ])
        
        # 1. Update active allocation record to returned
        for alloc in active_allocations:
            alloc.action_return_asset(check_in_notes=self.check_in_notes)

        # 2. Update asset details directly
        self.asset_id.write({
            'state': 'available',
            'condition': self.verified_condition
        })

        # 3. Write in-depth log entry
        self.env['assetflow.log'].create({
            'asset_id': self.asset_id.id,
            'action': 'return',
            'description': f"Returned & checked in. Verified condition: {self.verified_condition}. Notes: {self.check_in_notes}"
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

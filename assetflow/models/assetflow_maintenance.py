# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions

class AssetFlowMaintenance(models.Model):
    _name = 'assetflow.maintenance'
    _description = 'Asset Maintenance Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_requested desc'

    name = fields.Char(string='Maintenance Reference', copy=False, readonly=True, index=True)
    asset_id = fields.Many2one('assetflow.asset', string='Asset to Repair', required=True, tracking=True, index=True)
    description = fields.Text(string='Issue Description', required=True)
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Normal'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], string='Priority', default='medium', tracking=True)
    
    state = fields.Selection([
        ('draft', 'Draft Request'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved for Work'),
        ('in_progress', 'Repair In Progress'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', tracking=True, index=True)

    technician_id = fields.Many2one('hr.employee', string='Assigned Technician', tracking=True, index=True)
    date_requested = fields.Date(string='Date Requested', default=fields.Date.context_today, required=True, tracking=True)
    date_completed = fields.Date(string='Date Completed', tracking=True)
    repair_cost = fields.Float(string='Repair Cost', default=0.0, tracking=True)
    resolution_notes = fields.Text(string='Resolution / Repair Details')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('seq_assetflow_maintenance') or 'MAINT-0000'
        return super(AssetFlowMaintenance, self).create(vals_list)

    def action_submit(self):
        """Submit the draft request to pending."""
        self.write({'state': 'pending'})

    def action_approve(self):
        """Approve maintenance request and update asset state to maintenance."""
        for req in self:
            if req.state != 'pending':
                continue
            req.write({'state': 'approved'})
            # Update asset state to Under Maintenance
            req.asset_id.write({'state': 'maintenance'})
            
            # Log in-app notification
            self.env['assetflow.notification'].create({
                'name': 'Maintenance Approved',
                'description': f"Maintenance for asset {req.asset_id.asset_tag} has been approved.",
                'user_id': req.asset_id.employee_id.user_id.id or self.env.user.id,
                'state': 'unread'
            })
            req.message_post(body="Maintenance request approved. Asset moved to 'Under Maintenance'.")

    def action_reject(self):
        """Reject the request."""
        self.write({'state': 'rejected'})
        self.message_post(body="Maintenance request rejected.")

    def action_start_repair(self):
        """Mark repair in progress."""
        self.write({'state': 'in_progress'})

    def action_resolve(self, resolution_notes=False, cost=0.0):
        """Resolve maintenance request and reset asset state to available."""
        for req in self:
            req.write({
                'state': 'resolved',
                'date_completed': fields.Date.context_today(self),
                'resolution_notes': resolution_notes or req.resolution_notes or "Repairs completed successfully.",
                'repair_cost': cost or req.repair_cost
            })
            # Revert asset status back to available
            req.asset_id.write({
                'state': 'available',
                'condition': 'excellent' if req.priority == 'critical' else 'good'
            })
            # Log in-app notification
            self.env['assetflow.notification'].create({
                'name': 'Maintenance Resolved',
                'description': f"Maintenance work on asset {req.asset_id.asset_tag} is complete.",
                'user_id': req.asset_id.employee_id.user_id.id or self.env.user.id,
                'state': 'unread'
            })
            req.message_post(body="Maintenance resolved. Asset reverted to 'Available'.")
            
            # Track in global audit log
            self.env['assetflow.log'].create({
                'asset_id': req.asset_id.id,
                'action': 'maintenance',
                'description': f"Maintenance resolved. Cost: {req.repair_cost}. Notes: {req.resolution_notes}"
            })

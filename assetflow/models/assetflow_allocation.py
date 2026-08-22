# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions

class AssetFlowAllocation(models.Model):
    _name = 'assetflow.allocation'
    _description = 'Asset Allocation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_allocated desc'

    asset_id = fields.Many2one('assetflow.asset', string='Asset to Allocate', required=True, tracking=True, index=True)
    employee_id = fields.Many2one('hr.employee', string='Employee Recipient', tracking=True, index=True)
    department_id = fields.Many2one('hr.department', string='Department Recipient', tracking=True, index=True)
    
    date_allocated = fields.Date(string='Allocation Date', default=fields.Date.context_today, required=True, tracking=True)
    date_expected_return = fields.Date(string='Expected Return Date', tracking=True)
    date_returned = fields.Date(string='Actual Return Date', tracking=True)
    
    state = fields.Selection([
        ('requested', 'Transfer Requested'),
        ('approved', 'Approved'),
        ('active', 'Active Handout'),
        ('returned', 'Returned & Checked In'),
        ('overdue', 'Overdue Return')
    ], string='Status', default='requested', tracking=True, index=True)

    is_overdue = fields.Boolean(string='Is Overdue', compute='_compute_is_overdue', store=True, index=True)
    notes = fields.Text(string='Handout Notes')
    return_condition_notes = fields.Text(string='Check-In Condition Notes')
    
    # Asset Timeline Logger
    timeline_html = fields.Html(string='Asset Lifecycle Timeline', compute='_compute_timeline_html')

    @api.depends('date_expected_return', 'state', 'date_returned')
    def _compute_is_overdue(self):
        """Stored compute for overdue allocation tracking."""
        today = fields.Date.context_today(self)
        for alloc in self:
            if alloc.state in ['active', 'overdue'] and alloc.date_expected_return and alloc.date_expected_return < today:
                alloc.is_overdue = True
                if alloc.state != 'overdue':
                    alloc.write({'state': 'overdue'})
            else:
                alloc.is_overdue = False

    @api.model
    def _cron_check_overdue_allocations(self):
        """Cron job to check and mark allocations as overdue, sending notifications if needed."""
        today = fields.Date.context_today(self)
        overdue_allocs = self.search([
            ('state', '=', 'active'),
            ('date_expected_return', '<', today)
        ])
        for alloc in overdue_allocs:
            alloc.write({'state': 'overdue', 'is_overdue': True})
            # Log notification
            self.env['assetflow.notification'].create({
                'name': 'Allocation Overdue',
                'description': f"Asset {alloc.asset_id.asset_tag} is overdue for return.",
                'user_id': alloc.employee_id.user_id.id or self.env.user.id,
                'state': 'unread'
            })
            
            # Send Email Template if email templates are set up
            template = self.env.ref('assetflow.email_template_allocation_overdue', raise_if_not_found=False)
            if template:
                template.send_mail(alloc.id, force_send=True)


    @api.constrains('asset_id', 'state', 'employee_id', 'department_id')
    def _check_conflict_rules(self):
        """Conflict rule: Prevent allocating already taken assets."""
        for alloc in self:
            if alloc.state in ['approved', 'active', 'overdue']:
                # Find other active allocations for the same asset
                conflicting = self.search([
                    ('asset_id', '=', alloc.asset_id.id),
                    ('id', '!=', alloc.id),
                    ('state', 'in', ['approved', 'active', 'overdue'])
                ])
                if conflicting:
                    current_holder = conflicting[0].employee_id.name or conflicting[0].department_id.name or "another department"
                    raise exceptions.ValidationError(
                        f"Conflict Detected! Asset {alloc.asset_id.asset_tag} is currently held by {current_holder}. "
                        "To reallocate, please raise a Transfer Request instead."
                    )
                
                # Check asset model state directly
                if alloc.asset_id.state in ['allocated', 'maintenance', 'lost', 'retired', 'disposed']:
                    current_holder = alloc.asset_id.employee_id.name or alloc.asset_id.department_id.name or "another group"
                    raise exceptions.ValidationError(
                        f"Conflict: Asset {alloc.asset_id.asset_tag} is currently in '{alloc.asset_id.state}' state "
                        f"(held by {current_holder}). Cannot allocate directly."
                    )

    def action_approve(self):
        """Approve allocation request and update asset state."""
        for alloc in self:
            if alloc.state != 'requested':
                continue
            alloc.write({'state': 'approved'})
            alloc.asset_id.write({
                'state': 'allocated',
                'employee_id': alloc.employee_id.id,
                'department_id': alloc.department_id.id
            })
            # Log in-app notification
            self.env['assetflow.notification'].create({
                'name': 'Transfer Approved',
                'description': f"Asset {alloc.asset_id.asset_tag} transfer request has been approved.",
                'user_id': alloc.employee_id.user_id.id or self.env.user.id,
                'state': 'unread'
            })
            # Log history in chatter
            alloc.message_post(body=f"Allocation approved. Asset {alloc.asset_id.asset_tag} marked as Allocated.")

    def action_activate(self):
        """Mark allocation as active/handed out."""
        self.write({'state': 'active'})

    def action_return_asset(self, check_in_notes=False):
        """Custom return flow updating state and resetting asset to available."""
        for alloc in self:
            alloc.write({
                'state': 'returned',
                'date_returned': fields.Date.context_today(self),
                'return_condition_notes': check_in_notes or "Returned in normal condition."
            })
            # Reset asset state to available
            alloc.asset_id.write({
                'state': 'available',
                'employee_id': False,
                'department_id': False
            })
            # Log notification
            self.env['assetflow.notification'].create({
                'name': 'Asset Returned',
                'description': f"Asset {alloc.asset_id.asset_tag} has been returned and checked in.",
                'user_id': alloc.employee_id.user_id.id or self.env.user.id,
                'state': 'unread'
            })
            alloc.message_post(body="Asset returned. Status reverted to Available.")

    def _compute_timeline_html(self):
        """Generates dynamic visual timeline rendering for the Asset Passport."""
        for alloc in self:
            # Gather timeline logs
            logs = self.env['assetflow.log'].search([('asset_id', '=', alloc.asset_id.id)], order='create_date asc')
            html = '<div class="o_assetflow_timeline" style="padding: 10px; font-family: sans-serif;">'
            html += '<ul style="list-style-type: none; border-left: 2px solid #7C5BBA; padding-left: 20px; margin-left: 10px;">'
            for log in logs:
                date_str = log.create_date.strftime('%Y-%m-%d %H:%M')
                html += f'<li style="margin-bottom: 15px; position: relative;">'
                html += f'<span style="position: absolute; left: -26px; top: 2px; background: #7C5BBA; width: 10px; height: 10px; border-radius: 50%;"></span>'
                html += f'<strong>{date_str}</strong> - <span class="badge badge-info" style="background-color: #6c757d; color: white; padding: 2px 5px; border-radius: 3px;">{log.action}</span><br/>'
                html += f'<span style="color: #555;">{log.description} (by {log.user_id.name})</span>'
                html += '</li>'
            if not logs:
                html += '<li>No lifecycle logs recorded for this asset.</li>'
            html += '</ul></div>'
            alloc.timeline_html = html

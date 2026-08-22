# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions

class AssetFlowAudit(models.Model):
    _name = 'assetflow.audit'
    _description = 'Asset Audit Cycle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc'

    name = fields.Char(string='Audit Code', copy=False, readonly=True, index=True)
    department_id = fields.Many2one('hr.department', string='Scoped Department', help="Leave empty to audit all departments.")
    location = fields.Char(string='Scoped Location / Site')
    date_start = fields.Date(string='Start Date', default=fields.Date.context_today, required=True, tracking=True)
    date_end = fields.Date(string='Target End Date', tracking=True)
    
    state = fields.Selection([
        ('draft', 'Draft Cycle'),
        ('in_progress', 'Audit In Progress'),
        ('closed', 'Closed & Locked')
    ], string='Status', default='draft', tracking=True, index=True)

    auditor_ids = fields.Many2many('hr.employee', string='Assigned Auditors', tracking=True)
    line_ids = fields.One2many('assetflow.audit.line', 'audit_id', string='Checklist Lines')
    discrepancy_count = fields.Integer(string='Discrepancies', compute='_compute_discrepancies', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('seq_assetflow_audit') or 'AUDIT-0000'
        return super(AssetFlowAudit, self).create(vals_list)

    @api.depends('line_ids.is_discrepancy')
    def _compute_discrepancies(self):
        """Computed count of discrepancies found during the cycle."""
        for audit in self:
            audit.discrepancy_count = len(audit.line_ids.filtered(lambda l: l.is_discrepancy))

    def action_start_audit(self):
        """Populates audit checklist lines with all assets in scope."""
        self.ensure_one()
        self.write({'state': 'in_progress'})
        
        # Build scope query
        domain = [('state', 'not in', ['retired', 'disposed'])]
        if self.department_id:
            domain.append(('department_id', '=', self.department_id.id))
        if self.location:
            domain.append(('location', 'ilike', self.location))
            
        assets = self.env['assetflow.asset'].search(domain)
        
        # Clear existing lines
        self.line_ids.unlink()
        
        # Create checklist lines
        lines = []
        for asset in assets:
            lines.append((0, 0, {
                'asset_id': asset.id,
                'original_state': asset.state,
                'verified_condition': 'verified',
                'notes': ''
            }))
        self.write({'line_ids': lines})
        self.message_post(body=f"Audit cycle started. Scoped {len(assets)} assets into the checklist.")

    def action_close_audit(self):
        """Locks the cycle, auto-generates discrepancies, and updates affected asset states (Lost/Damaged)."""
        self.ensure_one()
        
        # Iterate over checklist and process discrepancies
        for line in self.line_ids:
            if line.verified_condition == 'missing':
                # Update asset status to lost
                line.asset_id.write({'state': 'lost'})
                self.env['assetflow.notification'].create({
                    'name': 'Audit Discrepancy: Missing Asset',
                    'description': f"Asset {line.asset_id.asset_tag} was marked missing during audit cycle {self.name}.",
                    'user_id': self.env.user.id,
                    'state': 'unread'
                })
            elif line.verified_condition == 'damaged':
                # Move to maintenance or log issue
                line.asset_id.write({'condition': 'poor'})
                self.env['assetflow.notification'].create({
                    'name': 'Audit Discrepancy: Damaged Asset',
                    'description': f"Asset {line.asset_id.asset_tag} was marked damaged during audit cycle {self.name}.",
                    'user_id': self.env.user.id,
                    'state': 'unread'
                })

            # Log audit results
            self.env['assetflow.log'].create({
                'asset_id': line.asset_id.id,
                'action': 'audit',
                'description': f"Audited in cycle {self.name}. Result: {line.verified_condition}. Notes: {line.notes}"
            })
            
        self.write({
            'state': 'closed',
            'date_end': fields.Date.context_today(self)
        })
        self.message_post(body="Audit cycle closed. Discrepancies processed and asset statuses updated.")


class AssetFlowAuditLine(models.Model):
    _name = 'assetflow.audit.line'
    _description = 'Audit Cycle Line'

    audit_id = fields.Many2one('assetflow.audit', string='Audit Cycle Reference', ondelete='cascade', required=True)
    asset_id = fields.Many2one('assetflow.asset', string='Asset Tag', required=True)
    original_state = fields.Char(string='Original Lifecycle State')
    verified_condition = fields.Selection([
        ('verified', 'Verified & Intact'),
        ('damaged', 'Damaged / Needs repair'),
        ('missing', 'Missing / Unaccounted')
    ], string='Audit Verdict', default='verified', required=True)
    notes = fields.Text(string='Auditor Comments')
    is_discrepancy = fields.Boolean(string='Is Discrepancy', compute='_compute_is_discrepancy', store=True)

    @api.depends('verified_condition')
    def _compute_is_discrepancy(self):
        """Computed flag showing true if the verdict indicates a discrepancy (damaged or missing)."""
        for line in self:
            line.is_discrepancy = line.verified_condition in ['damaged', 'missing']

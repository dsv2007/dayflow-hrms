# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AssetFlowAuditVerifyWizard(models.TransientModel):
    _name = 'assetflow.audit.verify.wizard'
    _description = 'Audit Verification Entry'

    audit_line_id = fields.Many2one('assetflow.audit.line', string='Audit Line Reference', required=True)
    asset_id = fields.Many2one('assetflow.asset', string='Asset', related='audit_line_id.asset_id', readonly=True)
    verified_condition = fields.Selection([
        ('verified', 'Verified & Intact'),
        ('damaged', 'Damaged / Needs repair'),
        ('missing', 'Missing / Unaccounted')
    ], string='Audit Verdict', default='verified', required=True)
    notes = fields.Text(string='Auditor Comments')

    @api.model
    def default_get(self, fields_list):
        res = super(AssetFlowAuditVerifyWizard, self).default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id and self.env.context.get('active_model') == 'assetflow.audit.line':
            res['audit_line_id'] = active_id
            line = self.env['assetflow.audit.line'].browse(active_id)
            res['verified_condition'] = line.verified_condition
            res['notes'] = line.notes
        return res

    def action_apply_verdict(self):
        """Applies auditor verdict to the audit line item."""
        self.ensure_one()
        self.audit_line_id.write({
            'verified_condition': self.verified_condition,
            'notes': self.notes
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

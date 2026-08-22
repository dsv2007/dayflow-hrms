# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AssetFlowLog(models.Model):
    _name = 'assetflow.log'
    _description = 'Asset History and Audit Trail Log'
    _order = 'create_date desc'

    asset_id = fields.Many2one('assetflow.asset', string='Asset Tag', required=True, ondelete='cascade', index=True)
    user_id = fields.Many2one('res.users', string='Performer', default=lambda self: self.env.user, required=True, index=True)
    action = fields.Selection([
        ('create', 'Asset Registered'),
        ('allocation', 'Asset Allocated'),
        ('transfer', 'Asset Transferred'),
        ('return', 'Asset Returned'),
        ('maintenance', 'Maintenance Action'),
        ('audit', 'Audit Checked')
    ], string='Action Type', required=True, index=True)
    description = fields.Text(string='Action Details', required=True)

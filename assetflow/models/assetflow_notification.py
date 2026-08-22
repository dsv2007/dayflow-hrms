# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AssetFlowNotification(models.Model):
    _name = 'assetflow.notification'
    _description = 'AssetFlow In-App Notification Center'
    _order = 'create_date desc'

    name = fields.Char(string='Notification Alert', required=True)
    description = fields.Text(string='Message Content', required=True)
    user_id = fields.Many2one('res.users', string='Recipient User', required=True, index=True)
    state = fields.Selection([
        ('unread', 'Unread Alert'),
        ('read', 'Acknowledged')
    ], string='Status', default='unread', required=True, index=True)
    
    def action_mark_read(self):
        """Allows user to acknowledge notifications."""
        self.write({'state': 'read'})

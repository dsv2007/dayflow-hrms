# -*- coding: utf-8 -*-
from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    dayflow_role = fields.Selection([
        ('employee', 'Employee'),
        ('hr_officer', 'HR Officer'),
        ('admin', 'Admin')
    ], string='Dayflow Role', default='employee', required=True, tracking=True)
    
    joining_date = fields.Date(string='Joining Date', default=fields.Date.context_today)

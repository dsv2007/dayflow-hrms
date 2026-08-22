# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions

class DayflowPayroll(models.Model):
    _name = 'dayflow.payroll'
    _description = 'Dayflow Employee Payroll Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'payroll_year desc, payroll_month desc'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, index=True, tracking=True)
    basic_salary = fields.Float(string='Basic Salary (₹)', default=0.0, required=True, tracking=True)
    allowances = fields.Float(string='Allowances (₹)', default=0.0, required=True, tracking=True)
    deductions = fields.Float(string='Deductions (₹)', default=0.0, required=True, tracking=True)
    net_salary = fields.Float(string='Net Salary (₹)', compute='_compute_net_salary', store=True, tracking=True)
    
    payroll_month = fields.Integer(string='Month (1-12)', required=True, default=lambda self: fields.Date.today().month)
    payroll_year = fields.Integer(string='Year', required=True, default=lambda self: fields.Date.today().year)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('paid', 'Paid')
    ], string='Status', default='draft', tracking=True, index=True)

    _employee_month_year_unique = models.UniqueIndex(
        "(employee_id, payroll_month, payroll_year)",
        "A payroll record already exists for this employee for the specified month and year!"
    )

    @api.depends('basic_salary', 'allowances', 'deductions')
    def _compute_net_salary(self):
        for rec in self:
            rec.net_salary = max(rec.basic_salary + rec.allowances - rec.deductions, 0.0)

    @api.constrains('payroll_month', 'payroll_year')
    def _check_dates_validity(self):
        for rec in self:
            if rec.payroll_month < 1 or rec.payroll_month > 12:
                raise exceptions.ValidationError("Payroll month must be between 1 and 12.")
            if rec.payroll_year < 2000 or rec.payroll_year > 2100:
                raise exceptions.ValidationError("Payroll year must be a realistic 4-digit year.")

    def action_approve(self):
        for rec in self:
            if rec.state != 'draft':
                raise exceptions.ValidationError("Only draft payrolls can be approved.")
            rec.write({'state': 'approved'})

    def action_pay(self):
        for rec in self:
            if rec.state != 'approved':
                raise exceptions.ValidationError("Only approved payrolls can be paid.")
            rec.write({'state': 'paid'})

# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions

class DayflowAttendance(models.Model):
    _name = 'dayflow.attendance'
    _description = 'Dayflow Attendance Log'
    _order = 'check_in desc'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, index=True)
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True, index=True)
    check_in = fields.Datetime(string='Check In', required=True)
    check_out = fields.Datetime(string='Check Out')
    worked_hours = fields.Float(string='Worked Hours (Hours)', compute='_compute_worked_hours', store=True)
    status = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('half_day', 'Half Day'),
        ('leave', 'Leave')
    ], string='Status', default='present', required=True)
    remarks = fields.Text(string='Remarks')

    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for rec in self:
            if rec.check_in and rec.check_out:
                duration = rec.check_out - rec.check_in
                rec.worked_hours = max(duration.total_seconds() / 3600.0, 0.0)
            else:
                rec.worked_hours = 0.0

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_attendance_dates(self):
        for rec in self:
            if rec.check_out and rec.check_in > rec.check_out:
                raise exceptions.ValidationError("Check-out time must be strictly after check-in time.")

    @api.model
    def action_check_in(self, employee_id):
        """Action for check-in via API or UI"""
        # Find active check-in (where check_out is null)
        active = self.search([
            ('employee_id', '=', employee_id),
            ('check_out', '=', False)
        ], limit=1)
        if active:
            raise exceptions.ValidationError("You are already checked in. Please check out first.")
        
        return self.create({
            'employee_id': employee_id,
            'check_in': fields.Datetime.now(),
            'date': fields.Date.context_today(self),
            'status': 'present'
        })

    @api.model
    def action_check_out(self, employee_id):
        """Action for check-out via API or UI"""
        active = self.search([
            ('employee_id', '=', employee_id),
            ('check_out', '=', False)
        ], limit=1)
        if not active:
            raise exceptions.ValidationError("No active check-in session found for this employee.")
        
        checkout_time = fields.Datetime.now()
        active.write({
            'check_out': checkout_time
        })
        return active

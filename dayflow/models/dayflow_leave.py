# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions

class DayflowLeave(models.Model):
    _name = 'dayflow.leave'
    _description = 'Dayflow Leave Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, index=True, tracking=True)
    leave_type = fields.Selection([
        ('sick', 'Sick Leave'),
        ('casual', 'Casual Leave'),
        ('earned', 'Earned Leave')
    ], string='Leave Type', default='sick', required=True, tracking=True)
    start_date = fields.Date(string='Start Date', required=True, tracking=True)
    end_date = fields.Date(string='End Date', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='pending', tracking=True, index=True)
    
    approver_id = fields.Many2one('hr.employee', string='Approver', readonly=True, tracking=True)
    approval_date = fields.Date(string='Approval Date', readonly=True)
    approver_comments = fields.Text(string='Approver Comments')
    rejection_reason = fields.Text(string='Rejection Reason')

    @api.constrains('start_date', 'end_date', 'employee_id', 'state')
    def _check_leave_dates(self):
        for rec in self:
            if rec.state == 'rejected':
                continue
            if rec.start_date and rec.end_date and rec.start_date > rec.end_date:
                raise exceptions.ValidationError("Start date must be before or equal to End date.")
            
            # Check for overlapping leave requests for the same employee
            overlap = self.search([
                ('employee_id', '=', rec.employee_id.id),
                ('id', '!=', rec.id),
                ('state', 'in', ['pending', 'approved']),
                ('start_date', '<=', rec.end_date),
                ('end_date', '>=', rec.start_date)
            ])
            if overlap:
                raise exceptions.ValidationError(
                    f"Conflict detected! You have an overlapping leave request ({overlap[0].leave_type}) "
                    f"from {overlap[0].start_date} to {overlap[0].end_date}."
                )

    def action_approve(self, approver_employee_id=False):
        """Approve the leave request."""
        # Standard Odoo context call or direct parameter
        approver = self.env['hr.employee'].browse(approver_employee_id) if approver_employee_id else self.env.user.employee_id
        for rec in self:
            if rec.state != 'pending':
                raise exceptions.ValidationError("Only pending leave requests can be approved.")
            rec.write({
                'state': 'approved',
                'approver_id': approver.id,
                'approval_date': fields.Date.context_today(self)
            })
            
            # Proactively update any attendance records on these dates to status='leave'
            # Or insert a placeholder leave log so check-in triggers won't count them as absent
            current_date = rec.start_date
            while current_date <= rec.end_date:
                # Check if attendance already exists
                attendance = self.env['dayflow.attendance'].search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('date', '=', current_date)
                ])
                if attendance:
                    attendance.write({'status': 'leave'})
                else:
                    self.env['dayflow.attendance'].create({
                        'employee_id': rec.employee_id.id,
                        'date': current_date,
                        'check_in': fields.Datetime.now(), # Placeholder
                        'check_out': fields.Datetime.now(),
                        'status': 'leave',
                        'remarks': f"Approved Leave: {rec.leave_type}"
                    })
                current_date = fields.Date.add(current_date, days=1)

    def action_reject(self, approver_employee_id=False):
        """Reject the leave request."""
        approver = self.env['hr.employee'].browse(approver_employee_id) if approver_employee_id else self.env.user.employee_id
        for rec in self:
            if rec.state != 'pending':
                raise exceptions.ValidationError("Only pending leave requests can be rejected.")
            if not rec.rejection_reason:
                raise exceptions.ValidationError("Please provide a Rejection Reason on the record before rejecting.")
            rec.write({
                'state': 'rejected',
                'approver_id': approver.id,
                'approval_date': fields.Date.context_today(self)
            })

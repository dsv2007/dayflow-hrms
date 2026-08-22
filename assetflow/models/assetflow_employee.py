# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    assetflow_role = fields.Selection([
        ('employee', 'Standard Employee'),
        ('dept_head', 'Department Head'),
        ('manager', 'Asset Manager'),
        ('admin', 'System Administrator')
    ], string='AssetFlow Role', default='employee', required=True, tracking=True, index=True)

    is_promoted = fields.Boolean(string='Promoted Role Active', default=False)

    @api.constrains('assetflow_role', 'department_id')
    def _check_dept_head(self):
        """Ensure a department head is assigned to their department correctly."""
        for emp in self:
            if emp.assetflow_role == 'dept_head' and emp.department_id:
                # Set department head link in hr.department
                emp.department_id.write({'manager_id': emp.id})

    def action_promote_to_manager(self):
        """Action for Admin to promote an employee to Asset Manager."""
        self.ensure_one()
        if not self.env.user.has_group('base.group_system') and self.env.user.employee_id.assetflow_role != 'admin':
            raise exceptions.UserError("Only System Administrators can assign or promote roles.")
        self.write({
            'assetflow_role': 'manager',
            'is_promoted': True
        })
        # Log active role changes in chatter
        self.message_post(body="Employee promoted to Asset Manager role.")

    def action_promote_to_dept_head(self):
        """Action to promote employee to Department Head."""
        self.ensure_one()
        if not self.env.user.has_group('base.group_system') and self.env.user.employee_id.assetflow_role != 'admin':
            raise exceptions.UserError("Only System Administrators can assign or promote roles.")
        self.write({
            'assetflow_role': 'dept_head',
            'is_promoted': True
        })
        self.message_post(body="Employee promoted to Department Head role.")

    def action_demote_to_employee(self):
        """Reset employee role back to standard Employee."""
        self.ensure_one()
        if not self.env.user.has_group('base.group_system') and self.env.user.employee_id.assetflow_role != 'admin':
            raise exceptions.UserError("Only System Administrators can demote roles.")
        self.write({
            'assetflow_role': 'employee',
            'is_promoted': False
        })
        self.message_post(body="Role demoted back to Standard Employee.")

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from datetime import date, timedelta

class TestDayflowLeave(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.department = cls.env['hr.department'].create({'name': 'Engineering'})
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee',
            'department_id': cls.department.id,
            'dayflow_role': 'employee',
        })
        cls.manager = cls.env['hr.employee'].create({
            'name': 'Test HR Manager',
            'department_id': cls.department.id,
            'dayflow_role': 'hr_officer',
        })

    def test_leave_overlap(self):
        """Test that overlapping leave requests raise ValidationError."""
        self.env['dayflow.leave'].create({
            'employee_id': self.employee.id,
            'leave_type': 'sick',
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=3),
        })

        # Overlapping subset
        with self.assertRaises(ValidationError):
            self.env['dayflow.leave'].create({
                'employee_id': self.employee.id,
                'leave_type': 'casual',
                'start_date': date.today() + timedelta(days=1),
                'end_date': date.today() + timedelta(days=2),
            })

    def test_leave_approval_cascade(self):
        """Test that approving a leave cascades to the attendance status."""
        leave = self.env['dayflow.leave'].create({
            'employee_id': self.employee.id,
            'leave_type': 'sick',
            'start_date': date.today(),
            'end_date': date.today(),
        })
        self.assertEqual(leave.state, 'pending')

        # Approve leave request
        leave.action_approve(approver_employee_id=self.manager.id)
        self.assertEqual(leave.state, 'approved')

        # Verify that an attendance record was created/updated with 'leave' status
        attendance = self.env['dayflow.attendance'].search([
            ('employee_id', '=', self.employee.id),
            ('date', '=', date.today())
        ])
        self.assertTrue(attendance)
        self.assertEqual(attendance.status, 'leave')

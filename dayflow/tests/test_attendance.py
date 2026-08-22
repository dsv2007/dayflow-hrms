from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class TestDayflowAttendance(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.department = cls.env['hr.department'].create({'name': 'Engineering'})
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee',
            'department_id': cls.department.id,
            'dayflow_role': 'employee',
        })

    def test_attendance_flow(self):
        """Test regular check-in, check-out, and worked hours calculation."""
        check_in_time = datetime.now() - timedelta(hours=8)
        attendance = self.env['dayflow.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': check_in_time,
            'status': 'present'
        })
        self.assertEqual(attendance.status, 'present')
        self.assertFalse(attendance.check_out)

        # Test check-out
        check_out_time = datetime.now()
        attendance.write({
            'check_out': check_out_time
        })
        self.assertAlmostEqual(attendance.worked_hours, 8.0, delta=0.1)

    def test_double_checkin_constraint(self):
        """Test that checking in twice without a check-out raises ValidationError."""
        self.env['dayflow.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': datetime.now() - timedelta(hours=2)
        })

        with self.assertRaises(ValidationError):
            self.env['dayflow.attendance'].create({
                'employee_id': self.employee.id,
                'check_in': datetime.now()
            })

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from psycopg2 import IntegrityError

class TestDayflowPayroll(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.department = cls.env['hr.department'].create({'name': 'Engineering'})
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee',
            'department_id': cls.department.id,
            'dayflow_role': 'employee',
        })

    def test_payroll_math(self):
        """Test net salary calculations and computed values."""
        payroll = self.env['dayflow.payroll'].create({
            'employee_id': self.employee.id,
            'payroll_month': '08',
            'payroll_year': '2026',
            'basic_salary': 5000.0,
            'allowances': 800.0,
            'deductions': 300.0,
        })
        self.assertEqual(payroll.net_salary, 5500.0)

    def test_payroll_unique_constraint(self):
        """Test that duplicate payroll for same month and year raises ValidationError."""
        self.env['dayflow.payroll'].create({
            'employee_id': self.employee.id,
            'payroll_month': '08',
            'payroll_year': '2026',
            'basic_salary': 5000.0,
        })

        # Try to duplicate for the same month/year
        with self.assertRaises(IntegrityError):
            self.env['dayflow.payroll'].create({
                'employee_id': self.employee.id,
                'payroll_month': '08',
                'payroll_year': '2026',
                'basic_salary': 4500.0,
            })

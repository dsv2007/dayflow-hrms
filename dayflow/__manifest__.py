# -*- coding: utf-8 -*-
{
    'name': 'Dayflow HRMS',
    'version': '1.0',
    'summary': 'Core Human Resource Management System for Hackathons',
    'description': """
Dayflow - Human Resource Management System
==========================================
Includes:
- Employee profile management (extends hr.employee)
- Attendance checking sequence (Check-In / Check-Out)
- Leave request management with overlap prevention
- Decoupled Payroll and salary calculation
- Computed HR insights
    """,
    'category': 'Human Resources/Dayflow',
    'depends': ['base', 'hr', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/dayflow_employee_views.xml',
        'views/dayflow_attendance_views.xml',
        'views/dayflow_leave_views.xml',
        'views/dayflow_payroll_views.xml',
        'views/dayflow_ai_views.xml',
        'views/dayflow_menus.xml',
        'data/dayflow_data.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}

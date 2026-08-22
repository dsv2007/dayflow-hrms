# -*- coding: utf-8 -*-
{
    'name': 'AssetFlow - Enterprise Asset & Resource Management',
    'version': '1.0',
    'summary': 'Streamline enterprise asset lifecycles, bookings, maintenance, audits, and actionable intelligence.',
    'description': """
AssetFlow Enterprise Asset & Resource Management System
======================================================
Key Features:
* Extended Employee/Department hierarchies.
* Complete Asset Passport (QR, Timeline, History, Risk, and Life metrics).
* Resource booking overlap validation.
* Maintenance routing & approval matrix.
* Structured Audit cycles & Discrepancy auto-generation.
* Command Center and Executive Insights panel.
* Gamified Department Leaderboard.
    """,
    'author': 'Antigravity Code Studio',
    'website': 'https://github.com/gemini-antigravity/assetflow',
    'category': 'Operations/AssetFlow',
    'depends': ['base', 'hr', 'mail', 'board', 'web'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/assetflow_sequence.xml',
        'data/assetflow_cron.xml',
        'data/mail_templates.xml',
        'wizards/assetflow_transfer_wizard_views.xml',
        'wizards/assetflow_return_wizard_views.xml',
        'wizards/assetflow_audit_verify_wizard_views.xml',
        'views/assetflow_department_views.xml',
        'views/assetflow_employee_views.xml',
        'views/assetflow_category_views.xml',
        'views/assetflow_asset_views.xml',
        'views/assetflow_allocation_views.xml',
        'views/assetflow_booking_views.xml',
        'views/assetflow_maintenance_views.xml',
        'views/assetflow_audit_views.xml',
        'views/assetflow_notification_views.xml',
        'views/assetflow_dashboard_views.xml',
        'views/assetflow_menus.xml',
        'report/assetflow_reports.xml',
        'report/assetflow_report_templates.xml',
        'report/assetflow_bi_report_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

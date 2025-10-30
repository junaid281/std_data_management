{
    'name': 'Student Management',
    'version': '1.0.0',
    'category': 'Education',
    'summary': 'Manage student information and generate reports',
    'description': """
        Student Management System
        ========================
        This module helps you manage student records, education history,
        and generate PDF reports.
    """,
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/student.xml',
        'views/wizard_view.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
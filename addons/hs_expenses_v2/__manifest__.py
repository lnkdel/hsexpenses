# -*- coding: utf-8 -*-
{
    'name': "hs_expenses_v2",

    'summary': """
        Marketing special hospitality application and reimbursement form""",

    'description': """
        Marketing special hospitality application and reimbursement form
    """,

    'author': "LiuJianyun",
    'website': "https://www.hscarbonfibre.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'HengShen Expense',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hs_base'],

    # always loaded
    'data': [
        'security/groups.xml',
        'security/rules.xml',
        'report/expense_reports.xml',
        'data/ir_sequence_data.xml',
        'data/preset_data.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/common.xml',
        'views/v1_menu.xml',
        'views/travel.xml',
        'views/travel2.xml',
        'views/entertain.xml',
        'views/special.xml',
        'views/templates.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
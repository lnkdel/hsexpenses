# -*- coding: utf-8 -*-
{
    'name': "hs_expenses",

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
        'data/ir_sequence_data.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',
        'views/views.xml',
        'views/common.xml',
        # 'views/templates.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
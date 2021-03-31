# -*- coding: utf-8 -*-
{
    'name': "hs_sales_lead",

    'summary': """
        This module is mainly used to record sales opportunities of Hengshen company.""",

    'description': """
        This module is mainly used to record sales opportunities of Hengshen company.
    """,

    'author': "LiuJianyun",
    'website': "https://www.hscarbonfibre.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'HengShen Sales',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hs_base'],

    # always loaded
    'data': [
        'data/ir_sequence_data.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
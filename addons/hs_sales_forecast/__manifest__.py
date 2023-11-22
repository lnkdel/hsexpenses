# -*- coding: utf-8 -*-
{
    'name': "hs_sales_forecast",

    'summary': """
        This module is mainly used to record sales forecast of Hengshen company.""",

    'description': """
        This module is mainly used to record sales forecast of Hengshen company.
    """,

    'author': "LiuJianyun",
    'website': "https://github.com/lnkdel",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'HengShen Sales',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hs_base', 'hs_sales_lead'],

    # always loaded
    'data': [
        'security/groups.xml',
        'views/views.xml',
        'views/sales_forecast.xml',
        # 'views/templates.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
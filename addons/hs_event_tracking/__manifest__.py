# -*- coding: utf-8 -*-
{
    'name': "hs_event_tracking",

    'summary': """
        事项追踪""",

    'description': """
        事项追踪
    """,

    'author': "LiuJianyun",
    'website': "https://www.hscarbonfibre.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'HengShen Event',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hs_base'],

    # always loaded
    'data': [
        'views/views.xml',
        'views/event_tracking.xml',
        'views/templates.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/ir.cron.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
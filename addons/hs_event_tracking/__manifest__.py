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
    'category': 'HengShen Event',
    'version': '0.1',
    'depends': ['hs_base'],
    'data': [
        'views/views.xml',
        'views/event_tracking.xml',
        'views/templates.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',
        'data/ir.cron.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
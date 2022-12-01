# -*- coding: utf-8 -*-
{
    'name': "hs_customer_profile",

    'summary': """
        客户档案管理""",

    'description': """
        客户档案管理
    """,

    'author': "LiuJianyun",
    'website': "https://www.hscarbonfibre.com",
    'category': 'HengShen Sales',
    'version': '0.1',
    'depends': ['hs_base','hs_expenses','hs_expenses_v2'],
    'data': [
        'security/groups.xml',
        'views/views.xml',
        'views/customer_profile.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',
        # 'data/ir.cron.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
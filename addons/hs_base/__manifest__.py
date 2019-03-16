# -*- coding: utf-8 -*-

{
    'name': 'HS - Base',
    'version': '0.1',
    'category': 'HengShen',
    'sequence': 80,
    'summary': 'Heng Shen Apps Base',
    'description': 'Heng Shen Apps Base',
    'author': "HSIT",
    'website': 'http://www.hscarbonfibre.com',
    'images': [
        'static/src/img/default_employee_image.png',
    ],
    'depends': [
        'mail',
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/hs_base_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}

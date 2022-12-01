# -*- coding: utf-8 -*-
from odoo import http

# class Hsexpenses/addons/hsCustomerProfile(http.Controller):
#     @http.route('/hsexpenses/addons/hs_customer_profile/hsexpenses/addons/hs_customer_profile/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hsexpenses/addons/hs_customer_profile/hsexpenses/addons/hs_customer_profile/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hsexpenses/addons/hs_customer_profile.listing', {
#             'root': '/hsexpenses/addons/hs_customer_profile/hsexpenses/addons/hs_customer_profile',
#             'objects': http.request.env['hsexpenses/addons/hs_customer_profile.hsexpenses/addons/hs_customer_profile'].search([]),
#         })

#     @http.route('/hsexpenses/addons/hs_customer_profile/hsexpenses/addons/hs_customer_profile/objects/<model("hsexpenses/addons/hs_customer_profile.hsexpenses/addons/hs_customer_profile"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hsexpenses/addons/hs_customer_profile.object', {
#             'object': obj
#         })
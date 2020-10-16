# -*- coding: utf-8 -*-
from odoo import http

# class Hsexpenses/addons/hsExpensesV2(http.Controller):
#     @http.route('/hsexpenses/addons/hs_expenses_v2/hsexpenses/addons/hs_expenses_v2/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hsexpenses/addons/hs_expenses_v2/hsexpenses/addons/hs_expenses_v2/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hsexpenses/addons/hs_expenses_v2.listing', {
#             'root': '/hsexpenses/addons/hs_expenses_v2/hsexpenses/addons/hs_expenses_v2',
#             'objects': http.request.env['hsexpenses/addons/hs_expenses_v2.hsexpenses/addons/hs_expenses_v2'].search([]),
#         })

#     @http.route('/hsexpenses/addons/hs_expenses_v2/hsexpenses/addons/hs_expenses_v2/objects/<model("hsexpenses/addons/hs_expenses_v2.hsexpenses/addons/hs_expenses_v2"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hsexpenses/addons/hs_expenses_v2.object', {
#             'object': obj
#         })
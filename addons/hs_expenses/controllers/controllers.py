# -*- coding: utf-8 -*-
from odoo import http

# class HsExpenses(http.Controller):
#     @http.route('/hs_expenses/hs_expenses/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hs_expenses/hs_expenses/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hs_expenses.listing', {
#             'root': '/hs_expenses/hs_expenses',
#             'objects': http.request.env['hs_expenses.hs_expenses'].search([]),
#         })

#     @http.route('/hs_expenses/hs_expenses/objects/<model("hs_expenses.hs_expenses"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hs_expenses.object', {
#             'object': obj
#         })
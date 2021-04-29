# -*- coding: utf-8 -*-
from odoo import http

# class HsSalesNotes(http.Controller):
#     @http.route('/hs_sales_notes/hs_sales_notes/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hs_sales_notes/hs_sales_notes/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hs_sales_notes.listing', {
#             'root': '/hs_sales_notes/hs_sales_notes',
#             'objects': http.request.env['hs_sales_notes.hs_sales_notes'].search([]),
#         })

#     @http.route('/hs_sales_notes/hs_sales_notes/objects/<model("hs_sales_notes.hs_sales_notes"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hs_sales_notes.object', {
#             'object': obj
#         })
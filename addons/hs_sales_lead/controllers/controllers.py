# -*- coding: utf-8 -*-
from odoo import http

# class HsSalesLead(http.Controller):
#     @http.route('/hs_sales_lead/hs_sales_lead/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hs_sales_lead/hs_sales_lead/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hs_sales_lead.listing', {
#             'root': '/hs_sales_lead/hs_sales_lead',
#             'objects': http.request.env['hs_sales_lead.hs_sales_lead'].search([]),
#         })

#     @http.route('/hs_sales_lead/hs_sales_lead/objects/<model("hs_sales_lead.hs_sales_lead"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hs_sales_lead.object', {
#             'object': obj
#         })
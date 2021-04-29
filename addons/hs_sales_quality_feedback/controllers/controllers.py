# -*- coding: utf-8 -*-
from odoo import http

# class HsSalesQualityFeedback(http.Controller):
#     @http.route('/hs_sales_quality_feedback/hs_sales_quality_feedback/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hs_sales_quality_feedback/hs_sales_quality_feedback/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hs_sales_quality_feedback.listing', {
#             'root': '/hs_sales_quality_feedback/hs_sales_quality_feedback',
#             'objects': http.request.env['hs_sales_quality_feedback.hs_sales_quality_feedback'].search([]),
#         })

#     @http.route('/hs_sales_quality_feedback/hs_sales_quality_feedback/objects/<model("hs_sales_quality_feedback.hs_sales_quality_feedback"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hs_sales_quality_feedback.object', {
#             'object': obj
#         })
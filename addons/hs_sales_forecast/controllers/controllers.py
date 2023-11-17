# -*- coding: utf-8 -*-
from odoo import http

# class HsSalesForecast(http.Controller):
#     @http.route('/hs_sales_forecast/hs_sales_forecast/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hs_sales_forecast/hs_sales_forecast/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hs_sales_forecast.listing', {
#             'root': '/hs_sales_forecast/hs_sales_forecast',
#             'objects': http.request.env['hs_sales_forecast.hs_sales_forecast'].search([]),
#         })

#     @http.route('/hs_sales_forecast/hs_sales_forecast/objects/<model("hs_sales_forecast.hs_sales_forecast"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hs_sales_forecast.object', {
#             'object': obj
#         })
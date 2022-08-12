# -*- coding: utf-8 -*-
from odoo import http

# class Hsexpenses/addons/hsEventTracking(http.Controller):
#     @http.route('/hsexpenses/addons/hs_event_tracking/hsexpenses/addons/hs_event_tracking/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hsexpenses/addons/hs_event_tracking/hsexpenses/addons/hs_event_tracking/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hsexpenses/addons/hs_event_tracking.listing', {
#             'root': '/hsexpenses/addons/hs_event_tracking/hsexpenses/addons/hs_event_tracking',
#             'objects': http.request.env['hsexpenses/addons/hs_event_tracking.hsexpenses/addons/hs_event_tracking'].search([]),
#         })

#     @http.route('/hsexpenses/addons/hs_event_tracking/hsexpenses/addons/hs_event_tracking/objects/<model("hsexpenses/addons/hs_event_tracking.hsexpenses/addons/hs_event_tracking"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hsexpenses/addons/hs_event_tracking.object', {
#             'object': obj
#         })
# -*- coding: utf-8 -*-
from odoo import http

# class Flowmanager(http.Controller):
#     @http.route('/flowmanager/flowmanager/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/flowmanager/flowmanager/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('flowmanager.listing', {
#             'root': '/flowmanager/flowmanager',
#             'objects': http.request.env['flowmanager.flowmanager'].search([]),
#         })

#     @http.route('/flowmanager/flowmanager/objects/<model("flowmanager.flowmanager"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('flowmanager.object', {
#             'object': obj
#         })
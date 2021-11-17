# -*- coding: utf-8 -*-
# from odoo import http


# class StockOilGestion(http.Controller):
#     @http.route('/stock_oil_gestion/stock_oil_gestion/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/stock_oil_gestion/stock_oil_gestion/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('stock_oil_gestion.listing', {
#             'root': '/stock_oil_gestion/stock_oil_gestion',
#             'objects': http.request.env['stock_oil_gestion.stock_oil_gestion'].search([]),
#         })

#     @http.route('/stock_oil_gestion/stock_oil_gestion/objects/<model("stock_oil_gestion.stock_oil_gestion"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('stock_oil_gestion.object', {
#             'object': obj
#         })

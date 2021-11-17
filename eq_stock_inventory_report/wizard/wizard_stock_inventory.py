# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from datetime import datetime, date
import xlsxwriter
import base64


class wizard_stock_inventory(models.TransientModel):
    _name = 'wizard.stock.inventory'
    _description = "Wizard Stock Inventory"

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouse')
    location_ids = fields.Many2many('stock.location', string='Location')
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    filter_by = fields.Selection([('product', 'Product'), ('category', 'Category')], string="Filter By")
    group_by_categ = fields.Boolean(string="Group By Category")
    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    name = fields.Char(string='File Name', readonly=True)
    data = fields.Binary(string='File', readonly=True)
    product_ids = fields.Many2many('product.product', string="Products")
    category_ids = fields.Many2many('product.category', string="Categories")

    @api.onchange('company_id')
    def onchange_company_id(self):
        domain = [('id', 'in', self.env.user.company_ids.ids)]
        if self.company_id:
            self.warehouse_ids = False
            self.location_ids = False
        return {'domain':{'company_id':domain}}

    @api.onchange('warehouse_ids')
    def onchange_warehouse_ids(self):
        stock_location_obj = self.env['stock.location']
        location_ids = stock_location_obj.search([('usage', '=', 'internal'), ('company_id', '=', self.company_id.id)])
        addtional_ids = []
        if self.warehouse_ids:
            for warehouse in self.warehouse_ids:
                addtional_ids.extend([y.id for y in stock_location_obj.search([('location_id', 'child_of', warehouse.view_location_id.id), ('usage', '=', 'internal')])])
            self.location_ids = False
        return {'domain':{'location_ids':[('id', 'in', addtional_ids)]}}

    def check_date_range(self):
        if self.end_date < self.start_date:
            raise ValidationError(_('End Date should be greater than Start Date.'))

    @api.onchange('filter_by')
    def onchange_filter_by(self):
        self.product_ids = False
        self.category_ids = False

    def print_report(self):
        self.check_date_range()
        datas = {'form':
                    {
                        'company_id': self.company_id.id,
                        'warehouse_ids': [y.id for y in self.warehouse_ids],
                        'location_ids': self.location_ids.ids or False,
                        'start_date': self.start_date,
                        'end_date': self.end_date,
                        'id': self.id,
                        'product_ids': self.product_ids.ids,
                        'product_categ_ids': self.category_ids.ids
                    },
                }
        return self.env.ref('eq_stock_inventory_report.action_stock_inventory_template').report_action(self, data=datas)

    def go_back(self):
        self.state = 'choose'
        return {
            'name': 'Stock Inventory Report',
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new'
        }

    def print_xls_report(self):
        self.check_date_range()
        xls_filename = 'stock_report.xlsx'
        workbook = xlsxwriter.Workbook('/tmp/' + xls_filename)
        report_stock_inv_obj = self.env['report.eq_stock_inventory_report.stock_inventory_report']

        header_merge_format = workbook.add_format({'bold':True, 'align':'center', 'valign':'vcenter', \
                                            'font_size':10, 'bg_color':'#D3D3D3', 'border':1})

        header_data_format = workbook.add_format({'align':'center', 'valign':'vcenter', \
                                                   'font_size':10, 'border':1})

        product_header_format = workbook.add_format({'valign':'vcenter', 'font_size':10, 'border':1})

        for warehouse in self.warehouse_ids:
            worksheet = workbook.add_worksheet(warehouse.name)
            worksheet.merge_range(0, 0, 2, 8, "Stock Report", header_merge_format)

            worksheet.set_column('A:B', 18)
            worksheet.set_column('C:H', 12)
            worksheet.write(5, 0, 'Company', header_merge_format)
            worksheet.write(5, 1, 'Warehouse', header_merge_format)
            worksheet.write(5, 2, 'Start Date', header_merge_format)
            worksheet.write(5, 3, 'End Date', header_merge_format)

            worksheet.write(6, 0, self.company_id.name, header_data_format)
            worksheet.write(6, 1, warehouse.name, header_data_format)
            worksheet.write(6, 2, str(self.start_date), header_data_format)
            worksheet.write(6, 3, str(self.end_date), header_data_format)

            if not self.location_ids:
                worksheet.merge_range(9, 0, 9, 1, "Products", header_merge_format)
                worksheet.write(9, 2, "Beginning", header_merge_format)
                worksheet.write(9, 3, "Received", header_merge_format)
                worksheet.write(9, 4, "Sales", header_merge_format)
                worksheet.write(9, 5, "Internal", header_merge_format)
                worksheet.write(9, 6, "Adjustments", header_merge_format)
                worksheet.write(9, 7, "Ending", header_merge_format)

                rows = 10
                prod_beginning_qty = prod_qty_in = prod_qty_out = prod_qty_int = prod_qty_adjust = prod_ending_qty = 0.00
                if not self.group_by_categ:
                    for product in report_stock_inv_obj._get_products(self):
                        beginning_qty = report_stock_inv_obj._get_beginning_inventory(self, product, warehouse)
                        product_val = report_stock_inv_obj.get_product_sale_qty(self, warehouse, product)
                        product_qty_in = product_val.get('product_qty_in')
                        product_qty_out = product_val.get('product_qty_out')
                        product_qty_internal = product_val.get('product_qty_internal')
                        product_qty_adjustment = product_val.get('product_qty_adjustment')

                        ending_qty = beginning_qty + product_qty_in + product_qty_out\
                                    + product_qty_internal + product_qty_adjustment

                        worksheet.merge_range(rows, 0, rows, 1, product.name_get()[0][1], product_header_format)
                        worksheet.write(rows, 2, beginning_qty, header_data_format)
                        worksheet.write(rows, 3, product_qty_in, header_data_format)
                        worksheet.write(rows, 4, abs(product_qty_out), header_data_format)
                        worksheet.write(rows, 5, product_qty_internal, header_data_format)
                        worksheet.write(rows, 6, product_qty_adjustment, header_data_format)
                        worksheet.write(rows, 7, ending_qty, header_data_format)

                        prod_beginning_qty += beginning_qty
                        prod_qty_in += product_qty_in
                        prod_qty_out += product_qty_out
                        prod_qty_int += product_qty_internal
                        prod_qty_adjust += product_qty_adjustment
                        prod_ending_qty += ending_qty
                        rows += 1

                    worksheet.merge_range(rows + 1, 0, rows + 1, 1, 'Total', header_merge_format)
                    worksheet.write(rows + 1, 2, prod_beginning_qty, header_merge_format)
                    worksheet.write(rows + 1, 3, prod_qty_in, header_merge_format)
                    worksheet.write(rows + 1, 4, abs(prod_qty_out), header_merge_format)
                    worksheet.write(rows + 1, 5, prod_qty_int, header_merge_format)
                    worksheet.write(rows + 1, 6, prod_qty_adjust, header_merge_format)
                    worksheet.write(rows + 1, 7, prod_ending_qty, header_merge_format)

                else:
                    rows += 1
                    product_val = report_stock_inv_obj.get_product_sale_qty(self, warehouse)
                    for categ, product_value in product_val.items():
                        categ_prod_beginning_qty = categ_prod_qty_in = categ_prod_qty_out = categ_prod_qty_int = categ_prod_qty_adjust = categ_prod_ending_qty = 0.00
                        worksheet.merge_range(rows, 0, rows, 7, self.env['product.category'].browse(categ).name, header_merge_format)
                        rows += 1
                        for product in product_value:
                            product_id = self.env['product.product'].browse(product['product_id'])
                            beginning_qty = report_stock_inv_obj._get_beginning_inventory(self, product_id.id, warehouse)

                            product_qty_in = product.get('product_qty_in')
                            product_qty_out = product.get('product_qty_out')
                            product_qty_internal = product.get('product_qty_internal')
                            product_qty_adjustment = product.get('product_qty_adjustment')

                            ending_qty = beginning_qty + product_qty_in + product_qty_out + product_qty_internal + product_qty_adjustment

                            worksheet.merge_range(rows, 0 , rows, 1, product_id.name_get()[0][1], product_header_format)
                            worksheet.write(rows, 2, beginning_qty, header_data_format)

                            worksheet.write(rows, 3, product_qty_in, header_data_format)
                            worksheet.write(rows, 4, abs(product_qty_out), header_data_format)
                            worksheet.write(rows, 5, product_qty_internal, header_data_format)
                            worksheet.write(rows, 6, product_qty_adjustment, header_data_format)
                            worksheet.write(rows, 7, ending_qty, header_data_format)

                            categ_prod_beginning_qty += beginning_qty
                            categ_prod_qty_in += product_qty_in
                            categ_prod_qty_out += product_qty_out
                            categ_prod_qty_int += product_qty_internal
                            categ_prod_qty_adjust += product_qty_adjustment
                            categ_prod_ending_qty += ending_qty
                            rows += 1

                        worksheet.merge_range(rows, 0 , rows, 1, 'Total', header_merge_format)
                        worksheet.write(rows, 2, categ_prod_beginning_qty, header_merge_format)
                        worksheet.write(rows, 3, categ_prod_qty_in, header_merge_format)
                        worksheet.write(rows, 4, abs(categ_prod_qty_out), header_merge_format)
                        worksheet.write(rows, 5, categ_prod_qty_int, header_merge_format)
                        worksheet.write(rows, 6, categ_prod_qty_adjust, header_merge_format)
                        worksheet.write(rows, 7, categ_prod_ending_qty, header_merge_format)

                        prod_qty_in += categ_prod_qty_in
                        prod_qty_out += categ_prod_qty_out
                        prod_qty_int += categ_prod_qty_int
                        prod_qty_adjust += categ_prod_qty_adjust
                        prod_ending_qty += categ_prod_ending_qty
                        prod_beginning_qty += categ_prod_beginning_qty
                        rows += 2

                    worksheet.merge_range(rows, 0, rows , 1, "Total", header_merge_format)
                    worksheet.write(rows, 2, prod_beginning_qty, header_merge_format)
                    worksheet.write(rows, 3, prod_qty_in, header_merge_format)
                    worksheet.write(rows, 4, abs(prod_qty_out), header_merge_format)
                    worksheet.write(rows, 5, prod_qty_int, header_merge_format)
                    worksheet.write(rows, 6, prod_qty_adjust, header_merge_format)
                    worksheet.write(rows, 7, prod_ending_qty, header_merge_format)
            else:
                worksheet.merge_range(9, 0, 9, 1, "Products", header_merge_format)
                worksheet.write(9, 2, "Location", header_merge_format)
                worksheet.write(9, 3, "Beginning", header_merge_format)
                worksheet.write(9, 4, "Received", header_merge_format)
                worksheet.write(9, 5, "Sales", header_merge_format)
                worksheet.write(9, 6, "Internal", header_merge_format)
                worksheet.write(9, 7, "Adjustments", header_merge_format)
                worksheet.write(9, 8, "Ending", header_merge_format)

                rows = 10
                prod_beginning_qty = prod_qty_in = prod_qty_out = prod_qty_int = prod_qty_adjust = prod_ending_qty = 0.00
                location_ids = report_stock_inv_obj.get_warehouse_wise_location(self, warehouse)
                if not self.group_by_categ:
                    for product in report_stock_inv_obj._get_products(self):
                        location_wise_data = report_stock_inv_obj.get_location_wise_product(self, warehouse, product, location_ids)
                        beginning_qty = location_wise_data[1][0]
                        product_qty_in = location_wise_data[1][1]
                        product_qty_out = location_wise_data[1][2]
                        product_qty_internal = location_wise_data[1][3]
                        product_qty_adjustment = location_wise_data[1][4]
                        ending_qty = location_wise_data[1][5]

                        worksheet.merge_range(rows, 0, rows, 1, product.display_name, product_header_format)
                        worksheet.write(rows, 2, '', header_data_format)
                        worksheet.write(rows, 3, beginning_qty, header_merge_format)
                        worksheet.write(rows, 4, product_qty_in, header_merge_format)
                        worksheet.write(rows, 5, abs(product_qty_out), header_merge_format)
                        worksheet.write(rows, 6, product_qty_internal, header_merge_format)
                        worksheet.write(rows, 7, product_qty_adjustment, header_merge_format)
                        worksheet.write(rows, 8, ending_qty, header_merge_format)
                        rows += 1

                        for location, value in location_wise_data[0].items():
                            worksheet.merge_range(rows, 0, rows, 1, '', header_data_format)

                            worksheet.write(rows, 2, location.display_name, header_data_format)
                            worksheet.write(rows, 3, value[0], header_data_format)
                            worksheet.write(rows, 4, value[1], header_data_format)
                            worksheet.write(rows, 5, abs(value[2]), header_data_format)
                            worksheet.write(rows, 6, value[3], header_data_format)
                            worksheet.write(rows, 7, value[4], header_data_format)
                            worksheet.write(rows, 8, value[5], header_data_format)
                            rows += 1

                        prod_beginning_qty += beginning_qty
                        prod_qty_in += product_qty_in
                        prod_qty_out += product_qty_out
                        prod_qty_int += product_qty_internal
                        prod_qty_adjust += product_qty_adjustment
                        prod_ending_qty += ending_qty

                    rows += 1
                    worksheet.merge_range(rows, 0, rows, 1, 'Total', header_merge_format)
                    worksheet.write(rows, 2, '', header_merge_format)
                    worksheet.write(rows, 3, prod_beginning_qty, header_merge_format)
                    worksheet.write(rows, 4, prod_qty_in, header_merge_format)
                    worksheet.write(rows, 5, abs(prod_qty_out), header_merge_format)
                    worksheet.write(rows, 6, prod_qty_int, header_merge_format)
                    worksheet.write(rows, 7, prod_qty_adjust, header_merge_format)
                    worksheet.write(rows, 8, prod_ending_qty, header_merge_format)

                else:
                    product_val = report_stock_inv_obj.get_product_sale_qty(self, warehouse)
                    for categ, product_value in product_val.items():
                        categ_prod_beginning_qty = categ_prod_qty_in = categ_prod_qty_out = categ_prod_qty_int = categ_prod_qty_adjust = categ_prod_ending_qty = 0.00
                        worksheet.merge_range(rows, 0, rows, 8, self.env['product.category'].browse(categ).name, header_merge_format)
                        rows += 1
                        for product in product_value:
                            product_id = self.env['product.product'].browse(product['product_id'])
                            location_wise_data = report_stock_inv_obj.get_location_wise_product(self, warehouse, product_id, location_ids)

                            beginning_qty = location_wise_data[1][0]
                            product_qty_in = location_wise_data[1][1]
                            product_qty_out = abs(location_wise_data[1][2])
                            product_qty_internal = location_wise_data[1][3]
                            product_qty_adjustment = location_wise_data[1][4]
                            ending_qty = location_wise_data[1][5]

                            worksheet.merge_range(rows, 0, rows, 1, product_id.display_name, product_header_format)
                            worksheet.write(rows, 2, '', header_data_format)
                            worksheet.write(rows, 3, beginning_qty, header_merge_format)
                            worksheet.write(rows, 4, product_qty_in, header_merge_format)
                            worksheet.write(rows, 5, product_qty_out, header_merge_format)
                            worksheet.write(rows, 6, product_qty_internal, header_merge_format)
                            worksheet.write(rows, 7, product_qty_adjustment, header_merge_format)
                            worksheet.write(rows, 8, ending_qty, header_merge_format)

                            rows += 1
                            for location, value in location_wise_data[0].items():
                                worksheet.merge_range(rows, 0, rows, 1, '', header_data_format)

                                worksheet.write(rows, 2, location.display_name, header_data_format)
                                worksheet.write(rows, 3, value[0], header_data_format)
                                worksheet.write(rows, 4, value[1], header_data_format)
                                worksheet.write(rows, 5, abs(value[2]), header_data_format)
                                worksheet.write(rows, 6, value[3], header_data_format)
                                worksheet.write(rows, 7, value[4], header_data_format)
                                worksheet.write(rows, 8, value[5], header_data_format)
                                rows += 1

                            categ_prod_beginning_qty += beginning_qty
                            categ_prod_qty_in += product_qty_in
                            categ_prod_qty_out += product_qty_out
                            categ_prod_qty_int += product_qty_internal
                            categ_prod_qty_adjust += product_qty_adjustment
                            categ_prod_ending_qty += ending_qty
                            rows += 1

                            worksheet.merge_range(rows, 0, rows , 1, "Total", header_merge_format)
                            worksheet.write(rows, 2, '', header_merge_format)
                            worksheet.write(rows, 3, categ_prod_beginning_qty, header_merge_format)

                        worksheet.write(rows, 4, categ_prod_qty_in, header_merge_format)
                        worksheet.write(rows, 5, categ_prod_qty_out, header_merge_format)
                        worksheet.write(rows, 6, categ_prod_qty_int, header_merge_format)
                        worksheet.write(rows, 7, categ_prod_qty_adjust, header_merge_format)
                        worksheet.write(rows, 8, categ_prod_ending_qty, header_merge_format)
                        rows += 2

        workbook.close()
        self.write({
            'state': 'get',
            'data': base64.b64encode(open('/tmp/' + xls_filename, 'rb').read()),
            'name': xls_filename
        })
        return {
            'name': 'Stock Inventory Report',
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new'
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

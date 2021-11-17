# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.float_utils import float_round, float_compare, float_is_zero
import logging
_logger = logging.getLogger(__name__)



class StockInventoryLineInherit(models.Model):
    _inherit = 'stock.inventory.line'



    difference_qty = fields.Float('Difference', compute='_compute_difference',
            help="Indicates the gap between the product's theoretical quantity and its newest quantity.",
            readonly=True, digits='Product Unit of Measure', search="_search_difference_qty", store="True")
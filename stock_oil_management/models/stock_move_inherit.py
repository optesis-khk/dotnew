# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.float_utils import float_round, float_compare, float_is_zero
import logging
_logger = logging.getLogger(__name__)



class StockMoveInherit(models.Model):
    _inherit = 'stock.move'
    
    quantity_done = fields.Float(compute="_get_volume_15_poids")
    volume_ambiant = fields.Float('Volume ambiant', default=0.0)
   # temperature = fields.Float('Temperature', default=0.0)
   # densite_15 = fields.Float('Densité à 15', digits='Coeff VCF decimal precision', default=0.0001)
   # coef_vcf = fields.Float('Coeff VCF', digits='Coeff VCF decimal precision', default=0.0001)
    temperature = fields.Float('Temperature', compute="_onchange_product_add_temperature",)
    densite_15 = fields.Float('Densité à 15', compute="_onchange_product_add_densite_15")
    coef_vcf = fields.Float('Coeff VCF', compute="_onchange_product_add_coef_vcf",default=0.0001)
    volume_15 = fields.Float('Volume à 15', compute="_get_volume_15_poids", inverse="_set_volume_15_poids", store=True)
    poids = fields.Float('Poids', compute="_get_volume_15_poids", inverse="_set_volume_15_poids", store=True)


    @api.onchange('product_id')
    def _onchange_product_add_temperature(self):
        for rec in self:
            if rec.product_id:
                self.temperature = rec.product_tmpl_id.temperature
    @api.onchange('product_id')
    def _onchange_product_add_densite_15(self):
        for rec in self:
            if rec.product_id:
                self.densite_15 = rec.product_tmpl_id.densite_15
    @api.onchange('product_id')
    def _onchange_product_add_coef_vcf(self):
        for rec in self:
            if rec.product_id:
                self.coef_vcf = rec.product_tmpl_id.coef_vcf


    def _set_volume_15_poids(self):
        for rec in self:
            if rec.product_id.black_product:
                rec.quantity_done = rec.poids
            else:
                rec.quantity_done = rec.volume_15
    
    @api.depends('volume_ambiant', 'coef_vcf', 'densite_15')
    def _get_volume_15_poids(self):
        for rec in self:
            _logger.info('LE TYPE DOPERATION EST DE KHK TEST AJUSTEMENT ' + str(rec.picking_id.picking_type_id.sequence_code))
            if rec.picking_id.picking_type_id.sequence_code not in ['IN', 'INT']:
                rec.volume_15 = rec.volume_ambiant * rec.coef_vcf
                rec.poids = rec.volume_ambiant * rec.densite_15 * rec.coef_vcf
                
            if rec.picking_id.picking_type_id.sequence_code == 'INT' and not rec.product_id.black_product:
                rec.volume_ambiant = rec.volume_15 / rec.coef_vcf
                rec.poids = rec.volume_15 * rec.densite_15
            if rec.picking_id.picking_type_id.sequence_code == 'INT' and rec.product_id.black_product:
                rec.volume_ambiant = rec.poids / (rec.densite_15 * rec.coef_vcf)
                
            if rec.picking_id.picking_type_id.sequence_code == 'IN' and rec.product_id.black_product:
                rec.quantity_done = rec.product_uom_qty = rec.poids
                
            if rec.picking_id.picking_type_id.sequence_code == 'IN' and not rec.product_id.black_product:
                rec.quantity_done = rec.product_uom_qty = rec.volume_15
            
            if rec.picking_id.picking_type_id.sequence_code:
                if rec.product_id.black_product:
                    rec.quantity_done = rec.product_uom_qty = rec.poids
                else:
                    rec.quantity_done = rec.product_uom_qty = rec.volume_15
            else:
                # this case for inventory ajustement
                rec.quantity_done = rec.product_qty

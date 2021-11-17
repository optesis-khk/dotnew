# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.float_utils import float_round
import logging
_logger = logging.getLogger(__name__)
    

class productProductInherit(models.Model):
    _inherit = 'product.product'
    
    coef_poids_calcule = fields.Float('Coefficient du poids calculé')

    temperature = fields.Float('Temperature',compute="_compute_temperature")
    densite_15 = fields.Float('Densité à 15', compute="_compute_densite_15")
    coef_vcf = fields.Float('Coeff VCF',compute="_compute_coef_vcf")

    def _compute_temperature(self):
        self.temperature = self.product_tmpl_id.temperature
    def _compute_densite_15(self):
        self.densite_15 = self.product_tmpl_id.densite_15
    def _compute_coef_vcf(self):
        self.coef_vcf = self.product_tmpl_id.coef_vcf
    
    def _compute_quantities(self):
        products = self.filtered(lambda p: p.type != 'service')
        res = products._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
        for product in products:
            product.qty_available = res[product.id]['qty_available']
            product.incoming_qty = res[product.id]['incoming_qty']
            product.outgoing_qty = res[product.id]['outgoing_qty']
            product.virtual_available = res[product.id]['virtual_available']
            product.free_qty = res[product.id]['free_qty']

        # Services need to be set with 0.0 for all quantities
        services = self - products
        services.qty_available = 0.0
        services.incoming_qty = 0.0
        services.outgoing_qty = 0.0
        services.virtual_available = 0.0
        services.free_qty = 0.0
    
    
class productTemplateInherit(models.Model):
    _inherit = 'product.template'
    
    volume_15_qty_available = fields.Float('Volume à 15', compute='_compute_quantities')
    poids_qty_available = fields.Float('Poids', compute='_compute_quantities')
    coef_poids_calcule = fields.Float('Coefficient du poids calculé', compute='_compute_coef_poids_calcule',
        inverse='_set_coef_poids_calcule', store=True)
    black_product = fields.Boolean('Est un produit noir')

    temperature = fields.Float('Temperature', default=0.0)
    densite_15 = fields.Float('Densité à 15', digits='Coeff VCF decimal precision', default=0.0001)
    coef_vcf = fields.Float('Coeff VCF', digits='Coeff VCF decimal precision', default=0.0001)
    
    def _set_coef_poids_calcule(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.coef_poids_calcule = template.coef_poids_calcule
    
    @api.depends('product_variant_ids', 'product_variant_ids.coef_poids_calcule')
    def _compute_coef_poids_calcule(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.coef_poids_calcule = template.product_variant_ids.coef_poids_calcule
        for template in (self - unique_variants):
            template.coef_poids_calcule = 0.0
    
    @api.depends_context('company_owned', 'force_company')
    def _compute_quantities(self):
        res = self._compute_quantities_dict()
        for template in self:
            template.qty_available = res[template.id]['qty_available']
            template.virtual_available = res[template.id]['virtual_available']
            template.incoming_qty = res[template.id]['incoming_qty']
            template.outgoing_qty = res[template.id]['outgoing_qty']

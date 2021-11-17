# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import ValidationError    

class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'
    
    @api.constrains('order_line')
    def _check_exist_product_in_line(self):
      for purchase in self:
          exist_product_list = []
          for line in purchase.order_line:
             if line.product_id.id in exist_product_list:
                raise ValidationError(_('Le produit doit être unique dans la ligne de commande'))
             exist_product_list.append(line.product_id.id)
    
    entrepot_id = fields.Many2one('stock.warehouse', string="Entrepôt")
    orde_chargement = fields.Char('Numéro Ordre Chargement')
    matricule_citerne_id = fields.Many2one('opt.transport')
    date_fin_carnet = fields.Date('Date fin validité carnet de jauge', related="matricule_citerne_id.date_fin_carnet")
    regime_douanier = fields.Many2one('opt.regime.douanier','Regime douanier')
    transporteur_id = fields.Many2one('hr.employee', 'Transporteur', related="matricule_citerne_id.transporteur_id")
    ptac_ptrac = fields.Float(string='PTAC/PTRAC', related="matricule_citerne_id.ptac_ptrac")
    poid_vide_camion = fields.Float(string='Poids vide', related="matricule_citerne_id.poids_vide")
    remplisseur_id = fields.Many2one('hr.employee', string='Remplisseur')
    num_ilot = fields.Many2one('opt.ilot', 'Numéro ILOT')
    poids_calcule = fields.Float('Poids calculé', compute="_get_weight_loaded")
    taux_majoration = fields.Float('Taux Majoration', default=0.0)
    ptac_ptrac_majore = fields.Float('PTAC/PTRAC Majoré', compute="_get_patc_ptrac_majore")
    compartiment_ids = fields.One2many('opt.transport.compartiment', 'sale_id', string="Remplissage par compartiment")
    heure_depot = fields.Datetime('Heure de dépot plan de chargement')
    #capacite_total_charge = fields.Float('Capacité total', compute="_get_weight_loaded", store=True)
    
    capacite_total_charge = fields.Float(string='Capacité total', digits='Product Unit of Measure', compute="_capacite_total")
    
    
    
    @api.onchange('capacite', 'compartiment_ids')
    def _capacite_total(self):
        for rec in self:
            total = sum(rec.compartiment_ids.mapped('capacite'))
            rec.capacite_total_charge = total
            
    nbre_capacite_total = fields.Float(string='nbre Compartiment', compute="_nbre_capacite_total")
    
    
    
    @api.onchange('compartiment_ids')
    def _nbre_capacite_total(self):
        for rec in self:
            count = 0
            for line in rec.compartiment_ids:
                count += 1
                rec.nbre_capacite_total = count
            
            
    
    @api.constrains('capacite_total_charge')
    def _check_loadead_capacity(self):
        for record in self:
            total = 0.0
            for line in record.order_line:
                total += line.volume_ambiant
            if record.capacite_total_charge > total:
                raise ValidationError(_("La quantité chargée ne doit pas être supérieur à la quantité vendue"))
    
    @api.depends('poids_calcule', 'taux_majoration')
    def _get_patc_ptrac_majore(self):
        for rec in self:
            rec.ptac_ptrac_majore = rec.ptac_ptrac * rec.taux_majoration / 100 + rec.ptac_ptrac
    
    @api.depends('compartiment_ids', 'ptac_ptrac')
    def _get_weight_loaded(self):
        for rec in self:
            total = 0.0
            poids_calcule = 0.0
            for C in rec.compartiment_ids:
                if C.product_id:
                    total += C.capacite
                    poids_calcule += C.capacite * C.product_id.coef_poids_calcule
            rec.capacite_total_charge = total
            rec.poids_calcule = poids_calcule + rec.poid_vide_camion
            
    @api.onchange('matricule_citerne_id')
    def _get_citerne_values(self):
        for rec in self:
            #rec.ptac_ptrac = False
            rec.date_fin_carnet = False
            rec.transporteur_id = False
            #rec.ptac_ptrac = rec.matricule_citerne_id.ptac_ptrac
            rec.date_fin_carnet = rec.matricule_citerne_id.date_fin_carnet
            rec.transporteur_id = rec.matricule_citerne_id.transporteur_id
            rec.compartiment_ids.unlink()
            for C in rec.matricule_citerne_id.compartiment_ids:
                self.env['opt.transport.compartiment'].create({
                    'name': C.name,
                    'sale_id': rec.id,
                    'capacite': C.capacite
                })
                
                
class SaleOrderInherit(models.Model):
    _inherit = 'sale.order.line'
    
    
    product_uom_qty = fields.Float(compute="_get_volume_15_poids")
    volume_ambiant = fields.Float('Volume ambiant', default=0.0)
    temperature = fields.Float('Temperature', default=0.0)
    densite_15 = fields.Float('Densité à 15', digits='Coeff VCF decimal precision', default=0.0)
    coef_vcf = fields.Float('Coeff VCF',digits='Coeff VCF decimal precision', default=0.0)
    volume_15 = fields.Float('Volume à 15', compute="_get_volume_15_poids", store=True)
    poids = fields.Float('Poids', compute="_get_volume_15_poids", store=True)

    @api.onchange('product_id')
    def _onchange_product_add_temperature(self):
        for rec in self:
                if rec.product_id:
                    self.temperature = rec.product_id.product_tmpl_id.temperature

    @api.onchange('product_id.temperature')
    def _set_temperature(self):
        for rec in self:
            if rec.product_id.temperature:
                self.temperature = self.product_id.temperature

    @api.onchange('product_id')
    def _onchange_product_add_densite_15(self):
        for rec in self:
            if rec.product_id:
                self.densite_15 = rec.product_id.product_tmpl_id.densite_15

    @api.onchange('product_id')
    def _onchange_product_add_coef_vcf(self):
        for rec in self:
            if rec.product_id:
                self.coef_vcf = rec.product_id.product_tmpl_id.coef_vcf
    
    @api.depends('volume_ambiant', 'coef_vcf', 'densite_15')
    def _get_volume_15_poids(self):
        for rec in self:
            rec.volume_15 = rec.volume_ambiant * rec.coef_vcf
            rec.poids = rec.volume_ambiant * rec.densite_15 * rec.coef_vcf
            if rec.product_id.black_product:
                rec.product_uom_qty = rec.poids
            else:
                rec.product_uom_qty = rec.volume_15
            
            
            
    def _prepare_procurement_values(self, group_id=False):
        """ Prepare specific key for moves or other components that will be created from a stock rule
        comming from a sale order line. This method could be override in order to add other custom key that could
        be used in move/po creation.
        """
        values = super(SaleOrderInherit, self)._prepare_procurement_values(group_id)
        self.ensure_one()
        date_planned = self.order_id.date_order\
            + timedelta(days=self.customer_lead or 0.0) - timedelta(days=self.order_id.company_id.security_lead)
        values.update({
            'group_id': group_id,
            'sale_line_id': self.id,
            'date_planned': date_planned,
            'route_ids': self.route_id,
            'warehouse_id': self.order_id.warehouse_id or False,
            'partner_id': self.order_id.partner_shipping_id.id,
            'company_id': self.order_id.company_id,
            'volume_ambiant': self.volume_ambiant,
            'temperature':self.temperature,
            'densite_15': self.densite_15,
            'coef_vcf':self.coef_vcf,
            'volume_15': self.volume_15,
            'poids': self.poids,
        })
        for line in self.filtered("order_id.commitment_date"):
            date_planned = fields.Datetime.from_string(line.order_id.commitment_date) - timedelta(days=line.order_id.company_id.security_lead)
            values.update({
                'date_planned': fields.Datetime.to_string(date_planned),
            })
        return values
        
        
    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            qty = line.volume_ambiant if not line.product_id.black_product else line.poids # we use volume_ambiant if product white elseif black we use poids
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups('account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])

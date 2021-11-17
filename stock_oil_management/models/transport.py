# -*- coding: utf-8 -*-

from odoo import models, fields, api
from openerp.exceptions import ValidationError
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)



class Transport(models.Model):
    _name = 'opt.transport'
    _description = 'Modele pour la gestion du transport'
    
    name = fields.Char('Matricule du citerne', required="True")
    poids_vide = fields.Float('Poids vide du citerne', required="True")
    ptac_ptrac = fields.Float('PTAC/PTRA', required="True")
    remork_matricule = fields.Char('Immatriculation de la remorque')
    date_fin_carnet = fields.Date('Date de fin validité carnet jauge')
    date_test = fields.Date('Date Test',default=datetime.today())
    transporteur_id = fields.Many2one('hr.employee', string='Transporteur', required="True")
    chauffeur_id = fields.Many2one('hr.employee', string='Chauffeur')
    telephone = fields.Char(string='Téléphone')
    num_cni = fields.Char(string='Numéro CNI')
    #compartiment_ids = fields.One2many('opt.transport.compartiment', 'transport_id', string="Compartiment et Capacité")
    
    #_sql_constraints = [('uniq_name', 'unique(name)', 'Le matricule doit etre unique!'),]
    
    compartiment_ids = fields.One2many('opt.transport.compartiment', 'transport_id', string="Compartiment et Capacité") 
    _sql_constraints = [
        ('uniq_name', 'unique(name)', 'Le matricule doit etre unique!'),
        ('date_fin_carnet_contraints', "CHECK(date_fin_carnet != date_test)", 'End date must be later than start date'),
    ]
   # @api.constrains('date_fin_carnet','date_test')
    #def _check_something(self):
     #   if self.date_fin_carnet > self.date_test:
      #      raise ValidationError("La Date de fin validité carnet jauge doit être inferieur a la date du jour %s " % self.date_fin_carnet)
    
    # all records passed the test, don't return anything

class TransportCompartiment(models.Model):
    _name = "opt.transport.compartiment"
    _description = "Modele pour les compartiment des camion"
    
    name = fields.Char('Compartiment')
    capacite = fields.Float('Capacité', default=0.0)
    transport_id = fields.Many2one('opt.transport')
    sale_id = fields.Many2one('sale.order')
    product_id = fields.Many2one('product.template')
    

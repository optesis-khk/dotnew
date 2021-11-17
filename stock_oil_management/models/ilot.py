# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class Ilot(models.Model):
    _name = 'opt.ilot'
    _description = 'Modele pour les Ilots'
    
    name = fields.Char('Numero ILOT', required="True")
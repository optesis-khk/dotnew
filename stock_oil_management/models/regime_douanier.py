# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.float_utils import float_round
import logging
_logger = logging.getLogger(__name__)
    

class RegimeDouanier(models.Model):
    _name = 'opt.regime.douanier'
    
    name = fields.Char('Régime douanier')
    
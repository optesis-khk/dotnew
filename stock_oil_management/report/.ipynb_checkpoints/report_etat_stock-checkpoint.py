# -*- coding:utf-8 -*-
# by khk
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError
from odoo import api, fields, models, _

class EtatStock(models.TransientModel):
    _name = 'report.stock_oil_management.report_etat_stock_view'
    _description = 'Rapport Etat des stock'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        pass
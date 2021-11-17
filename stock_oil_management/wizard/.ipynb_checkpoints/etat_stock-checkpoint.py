# -*- coding: utf-8 -*-
# by khk
import time
from datetime import datetime
from dateutil import relativedelta
from odoo import fields, models, api


class EtatStock(models.TransientModel):
    _name = 'opti.etat.stock'
    _description = "Wizard etat du stock"
    
    periode = fields.Date('Date de debut', required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    
    
    def print_report(self):
        active_ids = self.env.context.get('active_ids', [])
        datas = {
            'ids': active_ids,
            'model': 'opti.etat.stock',
            'form': self.read()[0]
        }
        return self.env.ref('stock_oil_management.etat_stock').report_action([], data=datas)
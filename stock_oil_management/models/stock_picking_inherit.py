# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
import logging
_logger = logging.getLogger(__name__)



class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'
    
    owner = fields.Many2one('res.partner', string="Attribuer un propriétaire")
    douan = fields.Many2one('opt.regime.douanier','Regime douanier', related="sale_id.regime_douanier")
    heure_debut = fields.Datetime(string="Heure début Chargement")
    heure_fin_charge = fields.Datetime(string="Heure fin chargement")
    date_debut = fields.Date('Date de debut')
    date_fin = fields.Date('Date de fin')
    heure_sortie = fields.Datetime(string="Heure de Sortie dépôt")
    entrepot_id = fields.Many2one('stock.warehouse', string="Entrepôt", related="sale_id.entrepot_id")
    orde_chargement = fields.Char('Numéro Ordre Chargement', related="sale_id.orde_chargement")
    matricule_citerne_id = fields.Many2one('opt.transport', related="sale_id.matricule_citerne_id")
    date_fin_carnet = fields.Date('Date fin validité carnet de jauge', related="sale_id.date_fin_carnet")
    regime = fields.Many2one('opt.regime.douanier','Regime douanier')
    transporteur_id = fields.Many2one('hr.employee', 'Transporteur', related="sale_id.transporteur_id")
    ptac_ptrac = fields.Float(string='PTAC/PTRAC', related="sale_id.ptac_ptrac")
    remplisseur_id = fields.Many2one('hr.employee', string='Remplisseur', related="sale_id.remplisseur_id")
    num_ilot = fields.Many2one('opt.ilot', 'Numéro ILOT', related="sale_id.num_ilot")
    poids_calcule = fields.Float('Poids calculé', related="sale_id.poids_calcule")
    taux_majoration = fields.Float('Taux Majoration', related="sale_id.taux_majoration")
    ptac_ptrac_majore = fields.Float('PTAC/PTRAC Majoré', related="sale_id.ptac_ptrac_majore")
    compartiment_ids = fields.One2many('opt.transport.compartiment', string="Remplissage par compartiment", related="sale_id.compartiment_ids")
    capacite_total_charge = fields.Float('Capacité total', related="sale_id.capacite_total_charge")

    
    def action_done(self):
        """Changes picking state to done by processing the Stock Moves of the Picking

        Normally that happens when the button "Done" is pressed on a Picking view.
        @return: True
        """
        """overrided t add volume_15 and poids in stock move create line 61? 62"""
        _logger.info('IN THE ACTION DONE FUCTION KHK')
        self._check_company()

        todo_moves = self.mapped('move_lines').filtered(lambda self: self.state in ['draft', 'waiting', 'partially_available', 'assigned', 'confirmed'])
        # Check if there are ops not linked to moves yet
        for pick in self:
            if pick.owner_id:
                pick.move_lines.write({'restrict_partner_id': pick.owner_id.id})
                pick.move_line_ids.write({'owner_id': pick.owner_id.id})

            # # Explode manually added packages
            # for ops in pick.move_line_ids.filtered(lambda x: not x.move_id and not x.product_id):
            #     for quant in ops.package_id.quant_ids: #Or use get_content for multiple levels
            #         self.move_line_ids.create({'product_id': quant.product_id.id,
            #                                    'package_id': quant.package_id.id,
            #                                    'result_package_id': ops.result_package_id,
            #                                    'lot_id': quant.lot_id.id,
            #                                    'owner_id': quant.owner_id.id,
            #                                    'product_uom_id': quant.product_id.uom_id.id,
            #                                    'product_qty': quant.qty,
            #                                    'qty_done': quant.qty,
            #                                    'location_id': quant.location_id.id, # Could be ops too
            #                                    'location_dest_id': ops.location_dest_id.id,
            #                                    'picking_id': pick.id
            #                                    }) # Might change first element
            # # Link existing moves or add moves when no one is related
            for ops in pick.move_line_ids.filtered(lambda x: not x.move_id):
                # Search move with this product
                moves = pick.move_lines.filtered(lambda x: x.product_id == ops.product_id)
                moves = sorted(moves, key=lambda m: m.quantity_done < m.product_qty, reverse=True)
                if moves:
                    ops.move_id = moves[0].id
                else:
                    new_move = self.env['stock.move'].create({
                                                    'name': _('New Move:') + ops.product_id.display_name,
                                                    'product_id': ops.product_id.id,
                                                    'product_uom_qty': ops.qty_done,
                                                    'volume_15': ops.volume_15,
                                                    'poids': ops.poids,
                                                    'product_uom': ops.product_uom_id.id,
                                                    'description_picking': ops.description_picking,
                                                    'location_id': pick.location_id.id,
                                                    'location_dest_id': pick.location_dest_id.id,
                                                    'picking_id': pick.id,
                                                    'picking_type_id': pick.picking_type_id.id,
                                                    'restrict_partner_id': pick.owner_id.id,
                                                    'company_id': pick.company_id.id,
                                                    })
                    ops.move_id = new_move.id
                    new_move._action_confirm()
                    todo_moves |= new_move
                    #'qty_done': ops.qty_done})
        todo_moves._action_done(cancel_backorder=self.env.context.get('cancel_backorder'))
        self.write({'date_done': fields.Datetime.now()})
        self._send_confirmation_email()
        return True
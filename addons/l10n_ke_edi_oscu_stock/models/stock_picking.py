# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import requests

from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError



class StockPicking(models.Model):
    _inherit = 'stock.picking'

    l10n_ke_validation_msg = fields.Json("Validation Message",
                                         compute='_compute_l10n_ke_validation_msg')
    l10n_ke_error_msg = fields.Json("Error message from sending", copy=False)
    l10n_ke_oscu_flow_type_code = fields.Selection(related='move_ids.l10n_ke_oscu_flow_type_code')
    l10n_ke_oscu_sar_number = fields.Integer(related='move_ids.l10n_ke_oscu_sar_number', readonly=True)
    l10n_ke_state = fields.Selection(selection=[('waiting_invoice', 'Waiting Invoice'), ('to_send', 'Not Sent Yet'), ('sent', 'Sent')],
                                     string="eTIMS Send Status",
                                     compute="_compute_l10n_ke_state")

    @api.depends("move_ids.l10n_ke_oscu_sar_number",
                 "move_ids.l10n_ke_oscu_flow_type_code",
                 "state",
                 "move_ids.purchase_line_id.invoice_lines.move_id.l10n_ke_oscu_invoice_number",
                 "move_ids.sale_line_id.invoice_lines.move_id.l10n_ke_oscu_invoice_number")
    def _compute_l10n_ke_state(self):
        for pick in self:
            if (pick.company_id.country_id.code != 'KE'
                    or not pick.l10n_ke_oscu_flow_type_code
                    or pick.state != 'done'
                    or all(m.product_id.type != 'product' for m in pick.move_ids)):
                pick.l10n_ke_state = False
                continue
            if all(m.l10n_ke_oscu_sar_number != 0 for m in pick.move_ids):
                pick.l10n_ke_state = 'sent'
            else:
                if pick.partner_id:
                    if pick.l10n_ke_oscu_flow_type_code in ('02', '12'): # Incoming Purchase
                        purchase_lines_to_check = pick.move_ids.purchase_line_id
                        related_invoices = purchase_lines_to_check.invoice_lines.move_id
                        unfinished_purchases = any(
                            pl.qty_received != pl.qty_invoiced and pl.product_id.type == 'product' for pl in
                            purchase_lines_to_check)
                        if unfinished_purchases or not related_invoices or any(not ri.l10n_ke_oscu_invoice_number for ri in related_invoices): #TODO: finetune
                            pick.l10n_ke_state = 'waiting_invoice'
                        else:
                            pick.l10n_ke_state = 'to_send'
                    elif pick.l10n_ke_oscu_flow_type_code in ('11', '03'): # Outgoing Sale or Return Incoming
                        sale_lines_to_check = pick.move_ids.sale_line_id
                        related_invoices = sale_lines_to_check.invoice_lines.move_id
                        unmatched_sale_lines = any(
                                sl.qty_delivered != sl.qty_invoiced and sl.product_id.type == 'product' for sl in sale_lines_to_check)
                        if unmatched_sale_lines or not related_invoices or any(not ri.l10n_ke_oscu_invoice_number for ri in related_invoices): #TODO: finetune
                            pick.l10n_ke_state = 'waiting_invoice'
                        else:
                            pick.l10n_ke_state = 'to_send'
                    elif pick.l10n_ke_oscu_flow_type_code == '01':
                        purchase_lines = pick.move_ids.mapped('purchase_line_id')
                        if purchase_lines:
                            purchase = purchase_lines[0].order_id
                            qty_imports = purchase._l10n_ke_calculate_imports_per_line(already_approved=True)
                            if any(l.qty_received != qty_imports[l] for l in purchase_lines): #TODO: UoM conversion
                                pick.l10n_ke_state = 'waiting_invoice'
                            else:
                                pick.l10n_ke_state = 'to_send'
                        else:
                            pick.l10n_ke_state = 'waiting_invoice'
                    else:
                        pick.l10n_ke_state = 'to_send'  # Inter branch e.g.
                else:
                    pick.l10n_ke_state = 'to_send'

    @api.depends('move_ids',
                 'move_ids.product_id',
                 'move_ids.product_id.unspsc_code_id',
                 'move_ids.product_id.l10n_ke_packaging_unit_id',
                 'move_ids.product_id.l10n_ke_origin_country_id',
                 'move_ids.product_id.l10n_ke_product_type_code',
                 'move_ids.product_uom',
                 'move_ids.l10n_ke_oscu_flow_type_code',
                 'l10n_ke_state')
    def _compute_l10n_ke_validation_msg(self):
        for pick in self:
            if (pick.company_id.account_fiscal_country_id.code != 'KE'
                    or not pick.move_ids
                    or not pick.move_ids[0].l10n_ke_oscu_flow_type_code):
                pick.l10n_ke_validation_msg = False
                continue
            pick_msg = {}
            msgs_prod = pick.move_ids.mapped('product_id')._l10n_ke_get_validation_messages()
            if msgs_prod:
                pick_msg.update({'prod_warning': msgs_prod})
            msgs_uom = (pick.move_ids.mapped('product_uom') | pick.move_ids.mapped('product_id.uom_id'))._l10n_ke_get_validation_messages()
            if msgs_uom:
                pick_msg.update({'uom_warning': msgs_uom})
            if pick.l10n_ke_state == 'waiting_invoice':
                pick_msg.update({'waiting_invoice': {'message': _('The invoice/customs import must be confirmed first before sending this picking. '), 'blocking': True}})
            pick.l10n_ke_validation_msg = pick_msg or False

    def _l10n_ke_action_open(self, title=None): # TODO: check where we can put it (if we still need it) as it won't block the pickings anymore
        pickings = self.search([
            ('state', '=', 'done'),
            ('move_ids.l10n_ke_oscu_flow_type_code', '!=', False),
            ('move_ids.l10n_ke_oscu_sar_number', '=', False),
         ], order='date') # TODO: add start date
        res = {
            'name': title or _("Pickings"),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'domain': [('id', 'in', pickings.ids)],
            'view_mode': 'tree',
            'views': [(self.env.ref('l10n_ke_edi_oscu_stock.stock_picking_tree_inherit_l10n_ke_edi_stock_special').id, 'tree'), (False, 'form')],
            'context': {'create': False, 'delete': False},
        }
        return res

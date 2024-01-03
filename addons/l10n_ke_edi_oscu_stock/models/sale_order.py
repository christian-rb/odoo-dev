# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _create_invoices(self, grouped=False, final=False, date=None):
        """ Make the link between credit note and original invoice when obvious"""
        moves = super()._create_invoices(grouped, final, date)
        if len(self) == 1 and len(moves) == 1 and moves.move_type in ('out_refund', 'in_refund'):
            original_invoices = self.invoice_ids - moves
            if len(original_invoices) == 1:
                moves.reversed_entry_id = original_invoices.id
        return moves

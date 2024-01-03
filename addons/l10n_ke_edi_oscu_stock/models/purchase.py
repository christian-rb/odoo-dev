# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    l10n_ke_customs_import_ids = fields.One2many('l10n_ke_edi.customs.import', 'purchase_id')


    def _l10n_ke_check_import(self, imp):
        # TODO: As we did the link through purchase order an purchase order line because the structure of the POs
        # is not necessarily the same as the customs imports, we should calculate with the total quantities for invoicing
        # and deliveries per product (taking into account UoM)
        self.ensure_one()
        if imp.product_id:
            qty_imports = self._l10n_ke_calculate_imports_per_line()
            lines = self.order_line.filtered(lambda l: l.product_id == imp.product_id)
            if not lines:
                return False
            all_lines_equal = True
            for line in lines:
                if qty_imports[line] != line.qty_received:
                    all_lines_equal = False #TODO could do an any/all here
            return all_lines_equal
        return False


    def _l10n_ke_calculate_imports_per_line(self, already_approved=False):
        self.ensure_one()
        qty_imports = {}
        lines = self.order_line
        for line in lines:
            qty_imports[line] = 0.0

        custom_imports = self.l10n_ke_customs_import_ids if not already_approved else self.l10n_ke_customs_import_ids.filtered(lambda c: c.state == '3')
        for imp in custom_imports:
            if not imp.product_id:
                continue
            if imp.uom_id:
                qty_product_uom = imp.uom_id._compute_quantity(imp.quantity, imp.product_id.uom_id)
            else:
                qty_product_uom = imp.quantity
            lines_same_product = lines.filtered(lambda l: l.product_id == imp.product_id)
            for line in lines_same_product:
                if not qty_product_uom:
                    continue
                if line.product_uom_qty - qty_imports[line] >= qty_product_uom or line == lines_same_product[-1]: #TODO: float_compare // line.product_uom_qty already in product UoM
                    qty_imports[line] += qty_product_uom
                    qty_product_uom = 0
                else:
                    qty_imports[line] = line.product_uom_qty
                    qty_product_uom -= (line.product_uom_qty - qty_imports[line])

        return qty_imports


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # Calculate the Purchase Order Line
    @api.depends('order_id', 'name')
    def _compute_display_name(self):
        for pol in self:
            pol.display_name = f"{pol.order_id.name} {pol.name}"

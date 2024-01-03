#m Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import json
import re
from datetime import datetime

from odoo.tools.float_utils import json_float_round

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # TODO docstrings/comments to explain the below _compute_* overrides
    def _compute_name(self):
        ke_amls = self.filtered(lambda l: l.move_id.l10n_ke_oscu_attachment_file)
        super(AccountMoveLine, self - ke_amls)._compute_name()

    def _compute_product_uom_id(self):
        ke_amls = self.filtered(lambda l: l.move_id.l10n_ke_oscu_attachment_file)
        super(AccountMoveLine, self - ke_amls)._compute_product_uom_id()

    def _compute_price_unit(self):
        ke_amls = self.filtered(lambda l: l.move_id.l10n_ke_oscu_attachment_file)
        super(AccountMoveLine, self - ke_amls)._compute_price_unit()

    def _compute_tax_ids(self):
        ke_amls = self.filtered(lambda l: l.move_id.l10n_ke_oscu_attachment_file)
        super(AccountMoveLine, self - ke_amls)._compute_tax_ids()

    def _l10n_ke_oscu_get_items(self, tax_details):
        # TODO docstring
        line_dict = {}
        per_record = tax_details['tax_details_per_record']
        for index, line in enumerate(self):
            product = line.product_id # for ease of reference
            product_uom_qty = line.product_uom_id._compute_quantity(line.quantity, product.uom_id)

            direction_modifier = -1 if line.move_id.move_type.startswith('out') else 1
            if line.quantity and line.discount != 100:
                price_subtotal_before_discount = line.balance / (1 - (line.discount / 100)) * direction_modifier
                price_unit = price_subtotal_before_discount / line.quantity
            else:
                price_unit = line.price_unit * direction_modifier
                price_subtotal_before_discount = price_unit * line.quantity
            discount_amount = price_subtotal_before_discount - (line.balance * direction_modifier)

            price_unit, price_subtotal_before_discount, discount_amount = abs(price_unit), abs(price_subtotal_before_discount), abs(discount_amount)

            line_dict[line.id] = {
                'itemSeq':   index+1,                                              # Line number
                'itemCd':    product.l10n_ke_item_code,                            # Item code as defined by us, of the form KE2BFTNE0000000000000039
                'itemClsCd': product.unspsc_code_id.code,                          # Item classification code, in this case the UNSPSC code
                'itemNm':    line.name,                                            # Item name
                'pkgUnitCd': product.l10n_ke_packaging_unit_id.code,               # Packaging code, describes the type of package used
                'pkg':       product_uom_qty / product.l10n_ke_packaging_quantity, # Number of packages used
                'qtyUnitCd': product.uom_id.l10n_ke_quantity_unit_id.code,         # The UOMs as defined by the KRA, defined seperately from the UOMs on the line
                'qty':       line.quantity,
                'prc':       price_unit,
                'splyAmt':   price_subtotal_before_discount,
                'dcRt':      line.discount,
                'dcAmt':     discount_amount,
                'taxTyCd':   line.tax_ids.filtered(lambda t: t.l10n_ke_tax_type_id).l10n_ke_tax_type_id.code,
                'taxblAmt':  per_record[line]['base_amount'],
                'taxAmt':    per_record[line]['tax_amount'],
                'totAmt':    per_record[line]['base_amount'] + per_record[line]['tax_amount'],
            }

            fields_to_round = ('pkg', 'qty', 'prc', 'splyAmt', 'dcRt', 'dcAmt', 'taxblAmt', 'taxAmt', 'totAmt')
            for field in fields_to_round:
                line_dict[line.id][field] = json_float_round(line_dict[line.id][field], 2)

            if product.barcode:
                line_dict[line.id].update({'bcd': product.barcode})
        return line_dict

    def _l10n_ke_get_validation_messages(self):
        """ Get the warning messages the lines.

        :returns: a dictionary of dictionaries, with each item representing a message, consisting
                  of the text of the message, an associated action and a name for the action.
        """
        messages = {}
        vat_rates = set(  # represents tax amounts for which the tax is considered VAT.
            rate['tax_rate'] for rate in self.env['l10n_ke_edi_oscu.code'].search([
                ('code_type', '=', '04')
            ]).read(['tax_rate'])
        )

        unspsc_tax_mismatch_products = self.env['product.product']
        for line in self:

            vat_taxes = line.tax_ids.filtered(lambda tax: (
                tax.amount in vat_rates and
                tax.amount_type in ('percent',)
            ))
            if not vat_taxes:
                continue

            if (
                (unspsc_tax_type := line.product_id.unspsc_code_id.l10n_ke_tax_type_id) and
                unspsc_tax_type.id != vat_taxes[0].l10n_ke_tax_type_id.id
            ):
                unspsc_tax_mismatch_products |= line.product_id

        if unspsc_tax_mismatch_products:
            messages['unspsc_tax_mismatch_warning'] = {
                'message': _(
                    'There are products in use with UNSPSC codes for which the KRA has specified a '
                    'different tax rate to that in use on the line.'
                ),
                'action_text': _("View Product(s)"),
                'action': self.env['product.product']._l10n_ke_action_open_products(unspsc_tax_mismatch_products.ids),
                'blocking': False,
            }
        return messages

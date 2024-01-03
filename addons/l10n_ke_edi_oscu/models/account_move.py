# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import json
import re
import requests
from datetime import datetime
from urllib.parse import urljoin

from odoo import _, api, Command, fields, models, modules, tools
from odoo.exceptions import UserError, ValidationError
from odoo.addons.base.models.ir_qweb_fields import Markup, nl2br, nl2br_enclose
from odoo.tools.float_utils import json_float_round


_logger = logging.getLogger(__name__)


TAX_CODE_LETTERS = ['A', 'B', 'C', 'D', 'E']


class AccountMove(models.Model):
    _inherit = 'account.move'

    # TODO - Reconsider field naming convention (l10n_ke_oscu every time?)
    #      - Add appropriate help strings for each field
    l10n_ke_oscu_confirmation_datetime = fields.Datetime(copy=False)
    l10n_ke_oscu_receipt_number = fields.Integer(string="Receipt Number", copy=False)
    l10n_ke_oscu_invoice_number = fields.Integer(string="Invoice Number", copy=False)
    l10n_ke_oscu_signature = fields.Char(string="Signature", copy=False)
    l10n_ke_oscu_datetime = fields.Datetime(string="Signing Time", copy=False)
    l10n_ke_oscu_internal_data = fields.Char(string="Internal Data", copy=False)
    l10n_ke_oscu_receipt_url = fields.Char(string="eTIMS Receipt URL", compute='_compute_l10n_ke_oscu_receipt_url')
    l10n_ke_control_unit = fields.Char(string="Control Unit ID")
    l10n_ke_oscu_attachment_file = fields.Binary(copy=False, attachment=True)
    l10n_ke_oscu_attachment_id = fields.Many2one(
        comodel_name='ir.attachment',
        string="FatturaPA Attachment",
        compute=lambda self: self._compute_linked_attachment_id('l10n_ke_oscu_attachment_id', 'l10n_ke_oscu_attachment_file'),
        depends=['l10n_ke_oscu_attachment_file'],
    )
    l10n_ke_reason_code_id = fields.Many2one(
        string="KRA Reason",
        comodel_name='l10n_ke_edi_oscu.code',
        domain="[('code_type', '=', '32')]", copy=False,
        help="Kenyan code for Credit Notes"
    )
    l10n_ke_payment_method_id = fields.Many2one(
        string="eTIMS Payment Method",
        comodel_name='l10n_ke_edi_oscu.code',
        domain="[('code_type', '=', '07')]",
        help="Method of payment communicated to the KRA via eTIMS. This is required when confirming purchases.",
    )
    l10n_ke_validation_message = fields.Json(compute='_compute_l10n_ke_validation_message')

    # TODO - These dependencies are about as messy as it gets, not sure anything can be done about them.
    @api.depends('invoice_line_ids.product_id',
                 'invoice_line_ids.product_id.unspsc_code_id',
                 'invoice_line_ids.product_id.l10n_ke_packaging_unit_id',
                 'invoice_line_ids.product_id.l10n_ke_origin_country_id',
                 'invoice_line_ids.product_id.l10n_ke_product_type_code',
                 'invoice_line_ids.product_uom_id')
    def _compute_l10n_ke_validation_message(self):
        """ Compute the series of messages to be displayed in the banner at the header of the invoice. """
        for move in self:
            if not move.company_id.l10n_ke_oscu_is_active or not move.move_type in (
                'in_invoice', 'out_invoice', 'in_refund', 'out_refund'
            ):
                move.l10n_ke_validation_message = False
                continue

            # TODO - This pattern constructs dictionaries containing representations of varying validation messages for each model.
            #        It would be good to enforce a consistency of structure in the output of the `_l10n_ke_get_validation_messages` for
            #        each implementation of the method.
            messages = {}
            if move.move_type in ('in_invoice', 'in_refund') and not move.l10n_ke_payment_method_id:
                messages.update({'no_payment_method_warning': {'message': _("An eTIMS payment method is required when confirming a purchase. "), 'blocking': True}})
            if move.move_type == 'out_refund' and not move.l10n_ke_reason_code_id:
                messages.update({'no_reason_code_warning': {'message': _("A KRA reason code is required when creating credit notes. "), 'blocking': True}})
            product_lines = move.invoice_line_ids.filtered(lambda line: line.display_type == 'product')
            if (invoice_line_messages := product_lines._l10n_ke_get_validation_messages()):
                messages.update(invoice_line_messages)
            if product_lines.filtered(lambda line: not line.product_id and line.name):
                messages.update({'no_product_warning': {'message': _("Some lines are missing a product where one must be set. "), 'blocking': True}})
            if (product_messages := move.invoice_line_ids.mapped('product_id')._l10n_ke_get_validation_messages(is_invoice=True)):
                messages.update({'product_warning': product_messages})
            if (uom_messages := move.invoice_line_ids.mapped('product_uom_id')._l10n_ke_get_validation_messages()):
                messages.update({'uom_warning': uom_messages})
            move.l10n_ke_validation_message = messages or {}

    def _post(self, soft=True):
        """Perform checks related to credit notes and set the confirmation datetime

        Unfortunately the KRA requires that this is performed here, as there is no validation of this
        kind their system. The purpose of these credit note checks is to confirm that niether the
        quantities nor the monetary amounts exceed their values on the source customer invoice.
        """
        # TODO - given the changes made to the flow, the coupling  of invoices with stock moves,
        #        I wonder if this still does what we need it to do or if it blocks unecessarily.
        #        Do we need to duplicate the same logic on the stock moves too? and if so, should
        #        these consistency checks be unified with the corresponding ones on stock and
        #        relocated to the sales/purchase order instead?

        def cumulative_quantity(quantity_dict, line):
            return (
                quantity_dict.setdefault(line.product_id, 0) +
                line.product_uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
            )

        for move in self.filtered(lambda move: move.country_code == 'KE' and move.reversed_entry_id):
            original_move = move.reversed_entry_id
            reversals = original_move.reversal_move_id
            original_lines, reverse_lines = original_move.invoice_line_ids, reversals.invoice_line_ids

            original_quantities, reverse_quantities = {}, {}

            for line in original_lines:
                original_quantities[line.product_id] = cumulative_quantity(original_quantities, line)
            for line in reverse_lines:
                reverse_quantities[line.product_id] = cumulative_quantity(reverse_quantities, line)

            exceeding_quantities = []
            for product, quantity in reverse_quantities.items():
                if product not in original_quantities:
                    exceeding_quantities.append(_("'%s' is not present on the original invoice.", product.name))
                elif (excess := quantity - original_quantities[product]) > 0:
                    exceeding_quantities.append(_("'%s' exceeds quantity on original invoice by %f %s", product.name, excess, product.uom_id.name))

            if exceeding_quantities:
                if len(reversals) > 1:
                    raise UserError(_(
                        "This credit note in conjunction with %s has items of a quantity exceeding "
                        "that of the original customer invoice %s. Please correct the quantity of "
                        "these lines before confirming:\n%s",
                        ', '.join((reversals - move).mapped("name")),
                        original_move.name,
                        '\n'.join(exceeding_quantities),
                        ))
                raise UserError(_(
                    "This credit note has items of a quantity exceeding that of the original "
                    "customer invoice %s. Please correct the quantity of these lines before "
                    "confirming:\n%s",
                    original_move.name,
                    '\n'.join(exceeding_quantities),
                ))

            credit_note_total = abs(sum(move.amount_total_in_currency_signed for move in reversals))
            excess = abs(credit_note_total) - abs(original_move.amount_total_in_currency_signed)

            if excess > 0:
                if len(reversals) > 1:
                    raise UserError(_(
                        "This credit note in conjunction with %s exceeds the amount on the original customer invoice %s. "
                        "Please adjust this credit note to a total value equal to or less than %d before confirming.",
                        ', '.join((reversals - move).mapped("name")),
                        original_move.name, abs(move.amount_total_in_currency_signed) - excess,
                    ))
                raise UserError(_(
                    "This credit note exceeds the amount of the original customer invoice %s. "
                    "Please adjust this credit note to a total value equal to or less than %d before confirming.",
                    original_move.name, abs(move.amount_total_in_currency_signed) - excess,
                ))

        self.l10n_ke_oscu_confirmation_datetime = fields.Datetime.now()  # TODO use confirmation datetime from service response
        return super()._post(soft)

    @api.depends('company_id.vat', 'company_id.l10n_ke_oscu_branch_code', 'l10n_ke_oscu_signature')
    def _compute_l10n_ke_oscu_receipt_url(self):
        for move in self:
            url = f"https://etims{'-sbx' if move.company_id.l10n_ke_server_mode == 'test' else ''}.kra.go.ke/common/link/etims/receipt/indexEtimsReceiptData?Data=%s"
            move.l10n_ke_oscu_receipt_url = url % ''.join([
                move.company_id.vat,
                move.company_id.l10n_ke_oscu_branch_code,
                move.l10n_ke_oscu_signature,
            ])

    def _l10n_ke_oscu_json_from_move(self):
        """ Get the json content of the TrnsSalesSaveWr/TrnsPurchaseSave request from a move. """
        self.ensure_one()

        confirmation_date = self.l10n_ke_oscu_confirmation_datetime and self.l10n_ke_oscu_confirmation_datetime.strftime('%Y%m%d%H%M%S') or ''
        invoice_date = self.invoice_date and self.invoice_date.strftime('%Y%m%d') or ''
        original_invoice_number = self.reversed_entry_id and self.reversed_entry_id.l10n_ke_oscu_invoice_number or 0
        tax_details = self._prepare_invoice_aggregated_taxes()
        line_items = self.invoice_line_ids._l10n_ke_oscu_get_items(tax_details)

        tax_codes = {item['code']: item['tax_rate'] for item in self.env['l10n_ke_edi_oscu.code'].search([('code_type', '=', '04')])}
        tax_rates = {f'taxRt{letter}': tax_codes.get(letter, 0) for letter in TAX_CODE_LETTERS}

        taxable_amounts = {
            f'taxblAmt{letter}': json_float_round(sum(
                [item['taxblAmt'] for item in line_items.values() if item['taxTyCd'] == letter]
            ), 2) for letter in TAX_CODE_LETTERS
        }
        tax_amounts = {
            f'taxAmt{letter}': json_float_round(sum(
                [item['taxAmt'] for item in line_items.values() if item['taxTyCd'] == letter]
            ), 2) for letter in TAX_CODE_LETTERS
        }

        content = {
            'invcNo':           '',                                        # KRA Invoice Number (set at the point of sending)
            'trdInvcNo':        (self.name or '')[:50],                            # Trader system invoice number
            'orgInvcNo':        original_invoice_number,                   # Original invoice number
            'cfmDt':            confirmation_date,                         # Validated date
            'pmtTyCd':          self.l10n_ke_payment_method_id.code or '',  # Payment type code
            'rcptTyCd': {                                                  # Receipt code
                'out_invoice':  'S',                                       # - Sale
                'out_refund':   'R',                                       # - Credit note after sale
                'in_invoice':   'P',                                       # - Purchase
                'in_refund':    'R',                                       # - Credit note after purchase
            }[self.move_type],
            **taxable_amounts,
            **tax_amounts,
            **tax_rates,
            'totTaxblAmt':      json_float_round(tax_details['base_amount'], 2),
            'totTaxAmt':        json_float_round(tax_details['tax_amount'], 2),
            'totAmt':           json_float_round(self.amount_total, 2),
            'totItemCnt':       len(line_items),                           # Total Item count
            'itemList':         list(line_items.values()),
            **self.company_id._l10n_ke_get_user_dict(self.create_uid, self.write_uid),
        }

        if self.move_type in ('in_invoice', 'in_refund'):
            content.update({
                'spplrTin':     (self.partner_id.vat or '')[:11],          # Supplier VAT
                'spplrNm':      (self.partner_id.name or '')[:60],         # Supplier name
                'regTyCd':      'M',                                       # Registration type code (Manual / Automatic)
                'pchsTyCd':     'N',                                       # Purchase type code (Copy / Normal / Proforma)
                'pchsSttsCd':   '02',                                      # Transaction status code TODO (02 approved / 05 credit note generated)
                'pchsDt':       invoice_date,                              # Purchase date
                # "spplrInvcNo": None,
            })
        else:
            receipt_part = {
                'custTin':      (self.partner_id.vat or '')[:11],          # Partner VAT
                'rcptPbctDt':   confirmation_date,                         # Receipt published date
                'prchrAcptcYn': 'N',                                       # Purchase accepted Yes/No
            }
            if self.partner_id.mobile:
                receipt_part.update({
                    'custMblNo': (self.partner_id.mobile or '')[:20]       # Mobile number, not required
                })
            if self.partner_id.contact_address_inline:
                receipt_part.update({
                    'adrs': (self.partner_id.contact_address_inline or '')[:200],  # Address, not required
                })
            content.update({
                'custTin':      (self.partner_id.vat or '')[:11],          # Partner VAT
                'custNm':       (self.partner_id.name or '')[:60],         # Partner name
                'salesSttsCd':  '02',                                      # Transaction status code TODO (same as pchsSttsCd)
                'salesDt':      invoice_date,                              # Sales date
                'prchrAcptcYn': 'Y',
                'receipt':      receipt_part,
            })
        if self.move_type in ('out_refund', 'in_refund'):
            content.update({'rfdRsnCd': self.l10n_ke_reason_code_id.code})
        return content

    def _l10n_ke_oscu_fetch_purchases(self, companies=None):
        """ Retrieve vendor bills from the KRA

        :param recordset companies: recordset containing comanies for which purchases should be
            fetched from the KRA.
        :returns: recordset of the fetched invoices
        """
        moves = self
        for company in companies:
            error, data, _date = company._l10n_ke_call_etims(
                'selectTrnsPurchaseSalesList',
                {'lastReqDt': company.l10n_ke_oscu_last_fetch_purchase_date or '20180101000000'}
            )
            if error:
                if error['code'] == '001':
                    _logger.warning('There are no new vendor bills on the OSCU for %s.', company.name)
                else:
                    _logger.error('Error retrieving purchases from the OSCU: %s: %s', error['code'], error['message'])
                continue

            for purchase in data['saleList']:
                filename = f"{purchase['spplrSdcId']}_{purchase['spplrInvcNo']}.json"
                existing = self.env['ir.attachment'].search([
                    ('name', '=', filename),
                    ('res_model', '=', 'account.move'),
                    ('res_field', '=', 'l10n_ke_oscu_attachment_file'),
                ])
                if existing:
                    _logger.warning('Vendor bill already exists: %s', filename)
                    continue

                move_type = {
                    'S': 'in_invoice',
                    'R': 'in_refund',
                }.get(purchase['rcptTyCd'], 'in_invoice')
                move = self.sudo().with_company(company).with_context(default_move_type=move_type).create({})
                attachment = self.sudo().env['ir.attachment'].create({
                    'name': filename,
                    'raw': json.dumps(purchase, indent=4),
                    'type': 'binary',
                    'res_model': 'account.move',
                    'res_id': move.id,
                    'res_field': 'l10n_ke_oscu_attachment_file',
                })
                move.invalidate_recordset(fnames=['l10n_ke_oscu_attachment_id', 'l10n_ke_oscu_attachment_file'])
                move.with_context(
                    account_predictive_bills_disable_prediction=True,
                    no_new_invoice=True,
                ).message_post(attachment_ids=attachment.ids)
                moves |= move

            company.l10n_ke_oscu_last_fetch_purchase_date = fields.Datetime.now().strftime('%Y%m%d%H%M%S')

        for move in moves:
            move._extend_with_attachments(move.l10n_ke_oscu_attachment_id, new=True)
            if not tools.config['test_enable'] and not modules.module.current_test:
                self.env.cr.commit()

        return moves

    def _cron_l10n_ke_oscu_fetch_purchases(self):
        """ Fetch purchases for all the relevant companies """
        companies = self.env['res.company'].search([('l10n_ke_oscu_is_active', '=', True)])
        moves = self._l10n_ke_oscu_fetch_purchases(companies)
        _logger.info(
            'Cron ran to fetch purchases for %i companies, and created %i vendor bills in the process.',
            len(moves.company_id),
            len(moves),
        )

    def _get_edi_decoder(self, file_data, new=False):
        # EXTENDS 'account'
        if file_data['type'] == 'binary':
            try:
                content = json.loads(file_data['content'])
                if all(key in content for key in (
                    'spplrTin', 'spplrNm', 'spplrBhfId', 'spplrInvcNo'
                )):
                    return self._l10n_ke_oscu_import_invoice
            except Exception:
                pass
        return super()._get_edi_decoder(file_data, new=new)

    def _l10n_ke_oscu_import_invoice(self, invoice, data, is_new):
        """ Decodes the json content from eTIMS into an Odoo move.

        This method is passed as the EDI decoder in the case where the file is recognised as an OSCU
        JSON representation of a vendor bill.

        :param dictionary data: the dictionary with the content to be imported
        :param boolean is_new:  whether the vendor bill is newly created or to be updated
        :returns:               the imported vendor bill
        """
        company = self.company_id
        content = json.loads(data['content'])
        message_to_log = []

        self.move_type = {
            'S': 'in_invoice',
            'R': 'in_refund',
        }.get(content['rcptTyCd'], 'in_invoice')

        branches = self.env['res.partner'].search([('vat', 'ilike', content['spplrTin'])])
        if (branch := branches.filtered(lambda branch: branch.l10n_ke_oscu_branch_code == content['spplrBhfId'])):
            self.partner_id = branch
        else:
            self.partner_id = self.env['res.partner'].create({
                'name': content['spplrNm'],
                'vat': content['spplrTin'],
                'l10n_ke_oscu_branch_code': content['spplrBhfId'],
            })
            message_to_log.append(_(
                "A vendor with a matching Tax ID and Branch ID was not found. "
                "One with the corresponding details was created."
            ))
            message_to_log.append("")

        self.invoice_date = datetime.strptime(content['salesDt'], '%Y%m%d').date()
        self.l10n_ke_control_unit = content['spplrSdcId']

        lines_dict = self.env['product.product']._l10n_ke_assign_products_from_json(
            {item['itemSeq']: item for item in content['itemList']}
        )

        tax_rate_map = {code: content[f'taxRt{code}'] for code in TAX_CODE_LETTERS}
        uom_codes = [line['qtyUnitCd'] for line in lines_dict.values()]
        uom_map = {
            unit_code.code: uom_id
            for unit_code, uom_id in self.env['uom.uom']._read_group(
                domain=[('l10n_ke_quantity_unit_id.code', 'in', uom_codes)],
                groupby=['l10n_ke_quantity_unit_id'],
                aggregates=['id:min'],
            )
        }
        for item in lines_dict.values():
            if (taxes := item.get('product') and item['product'].supplier_taxes_id.filtered(lambda tax: tax.company_id == self.company_id)):
                for tax in taxes:
                    if tax.l10n_ke_tax_type_id.code == item['taxTyCd'] and tax.amount == tax_rate_map[item['taxTyCd']]:
                        item['tax'] = tax
                        break

            # If we can't select a tax from the product,
            if not item.get('tax'):
                item['tax'] = self.env['account.tax'].search([
                    ('type_tax_use', '=', 'purchase'),
                    ('company_id', '=', self.company_id.id),
                    ('l10n_ke_tax_type_id.code', '=', item['taxTyCd']),
                    ('amount', '=', tax_rate_map[item['taxTyCd']]),
                ], limit=1)

            # If we don't already have a matching UoM from the product
            if item.get('uom_code') != item['qtyUnitCd']:
                if (uom_id := uom_map.get(item['qtyUnitCd'])):
                    item['uom_id'] = uom_id
                else:
                    item['uom_id'] = self.env.ref('uom.product_uom_unit').id

        self.invoice_line_ids = [Command.create({
            'product_id':     item['product'].id if item['product'] else None,
            'sequence':       sequence * 10,
            'name':           item['itemNm'],
            'quantity':       item['qty'],
            'product_uom_id': item['uom_id'],
            'price_unit':     item['prc'],
            'discount':       item['dcRt'],
            'tax_ids':        [item['tax'].id] if item['tax'] else None,
        }) for sequence, item in lines_dict.items()]
        message_to_log += [item['message'] for item in lines_dict.values() if item.get('message')]
        message = Markup("<br/>").join(message for message in message_to_log)
        # for message in message_to_log:
        self.sudo().message_post(body=message)
        return True

    def _l10n_ke_oscu_json_from_attachment(self):
        """Get the json content of the TrnsPurchaseSave request given an on the move."""

        self.ensure_one()
        if not self.l10n_ke_oscu_attachment_id:
            return {}

        file_content = json.loads(self.l10n_ke_oscu_attachment_id.raw)
        if not all(key in file_content for key in (
            'spplrTin', 'spplrNm', 'spplrBhfId', 'spplrInvcNo'
        )):
            return {}

        # Firstly, those fields that map directly from the file to the purchase confirmation request
        content = {field: file_content[field] for field in (
            'spplrTin', 'spplrNm', 'spplrBhfId',
            'spplrInvcNo', 'pmtTyCd', 'totItemCnt',
            'taxblAmtA', 'taxRtA', 'taxAmtA',
            'taxblAmtB', 'taxRtB', 'taxAmtB',
            'taxblAmtC', 'taxRtC', 'taxAmtC',
            'taxblAmtD', 'taxRtD', 'taxAmtD',
            'taxblAmtE', 'taxRtE', 'taxAmtE',
            'totTaxblAmt', 'totTaxAmt', 'totAmt',
        )}

        confirmation_date = self.l10n_ke_oscu_confirmation_datetime and self.l10n_ke_oscu_confirmation_datetime.strftime('%Y%m%d%H%M%S')
        content.update({
            'invcNo':     '',
            'orgInvcNo':   0,                                              # TODO think about this
            'regTyCd':    'M',                                             # Registration type: manual
            'pchsTyCd':   'N',                                             # Purchase type: normal
            'pchsSttsCd': '02',                                            # Transaction progress: Accepted
            'pchsDt':     file_content['salesDt'],
            'cfmDt':      confirmation_date,                               # Validated date
            **self.company_id._l10n_ke_get_user_dict(self.create_uid, self.write_uid),
        })

        item_list = []
        for file_item in file_content['itemList']:
            item = {field: file_item[field] for field in (
                'itemSeq', 'itemClsCd', 'itemNm', 'pkgUnitCd', 'bcd', 'pkg', 'qtyUnitCd', 'qty',
                'prc', 'splyAmt', 'dcRt', 'dcAmt', 'taxblAmt', 'taxTyCd', 'taxAmt', 'totAmt',
            )}
            item.update({
                'itemCd': '',
                'spplrItemCd':    file_item['itemCd'],
                'supplrItemNm':   file_item['itemNm'],
                'spplrItemClsCd': file_item['itemClsCd'],
            })
            item_list.append(item)

        content['itemList'] = item_list
        return content

    def _l10n_ke_oscu_send_customer_invoice(self):
        company = self.company_id

        content = {}
        content.update(self._l10n_ke_oscu_json_from_move())
        content.update({'invcNo': company._l10n_ke_get_invoice_sequence(self.move_type).number_next})  # KRA Invoice Number

        error, data, _date = company._l10n_ke_call_etims('saveTrnsSalesOsdc', content)
        if self.is_sale_document() and not error:
            self.write({
                'l10n_ke_oscu_receipt_number': data['curRcptNo'],
                'l10n_ke_oscu_invoice_number': content['invcNo'],
                'l10n_ke_oscu_signature': data['rcptSign'],
                'l10n_ke_oscu_datetime': datetime.strptime(data['sdcDateTime'], '%Y%m%d%H%M%S'),
                'l10n_ke_oscu_internal_data': data['intrlData'],
                'l10n_ke_control_unit': company.l10n_ke_control_unit,
            })
        company._l10n_ke_get_invoice_sequence().next_by_id() #TODO: we need a better thing here: best would be to assign it before sending
        return content, error

    def action_l10n_ke_oscu_confirm_vendor_bill(self):
        """Send vendor bill information to the KRA in order to confirm that it has been accepted

        Vendor bills can be received from the OSCU or created locally. When confirming vendor bills
        received from the KRA, we can use the information from the attachment used to generate the
        invoice in the first place to create the request. If the invoice is created locally,
        generate the request using just the fields on the vendor bill.
        """
        for move in self:
            if (blocking := [msg for msg in (move.l10n_ke_validation_message or {}).values() if msg.get('blocking')]):
                raise UserError(_("Please resolve these issues first.\n") + '\n'.join([f"- {msg['message']}" for msg in blocking]))
            company = move.company_id
            content = {}

            if move.l10n_ke_oscu_attachment_id:
                content.update(move._l10n_ke_oscu_json_from_attachment())
                content['rcptTyCd'] = {'in_invoice': 'P', 'in_refund': 'R'}.get(move.move_type)
                content['regTyCd'] = 'A'
                if not content['pmtTyCd']:
                    content['pmtTyCd'] = move.l10n_ke_payment_method_id.code
            else:
                content.update(move._l10n_ke_oscu_json_from_move())
            content.update({'invcNo': company._l10n_ke_get_invoice_sequence(move.move_type).next_by_id()})

            error, data, _date = company._l10n_ke_call_etims('insertTrnsPurchase', content)

            if error:
                raise UserError(error['message'])

            move.l10n_ke_oscu_invoice_number = move.id
            move.message_post(body=_("Purchase confirmed on eTIMS."))
            company._l10n_ke_get_invoice_sequence(move.move_type).next_by_id()

    # Invoice formatting
    def _get_name_invoice_report(self):
        # EXTENDS account
        self.ensure_one()
        if self.l10n_ke_oscu_invoice_number:
            return 'l10n_ke_edi_oscu.report_invoice_document'
        return super()._get_name_invoice_report()

    @api.model
    def _l10n_ke_hyphenate_invoice_field(self, to_hyphenate, hyphenate_by=4):
        """Hyphenates a string by a regular interval

        :param str to_hyphenate: string to be hyphenated (e.g. 'abcdefghijklmnop' becomes 'abcd-efgh-ijkl-mnop')
        :param int hyphenate_by: the regular interval at which to add a hyphen
        """

        hyphenate_range = (str_len := len(to_hyphenate)) and range(str_len//hyphenate_by + (1 if str_len % hyphenate_by else 0)) or []
        return '-'.join(to_hyphenate[(i*hyphenate_by):(i*hyphenate_by)+hyphenate_by] for i in hyphenate_range)

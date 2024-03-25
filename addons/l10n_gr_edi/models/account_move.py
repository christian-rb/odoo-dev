# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _, api
from odoo.addons.l10n_gr_edi.models.classification_data import (
    CLASSIFICATION_CATEGORY_EXPENSE, INVOICE_TYPES_SELECTION, INVOICE_TYPES_HAVE_INCOME, INVOICE_TYPES_HAVE_EXPENSE,
    TYPES_WITH_CORRELATE_INVOICE, COMBINATIONS_WITH_POSSIBLE_EMPTY_TYPE, VALID_TAX_AMOUNTS,
    TYPES_WITH_FORBIDDEN_COUNTERPART, TYPES_WITH_VAT_EXEMPT, TYPES_WITH_VAT_CATEGORY_8,
)


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_gr_edi_mark = fields.Char(string='MyDATA Mark')
    l10n_gr_edi_state = fields.Selection(related='l10n_gr_edi_active_document_id.state')
    l10n_gr_edi_message = fields.Char(related='l10n_gr_edi_active_document_id.message')
    l10n_gr_edi_inv_type = fields.Selection(
        selection=INVOICE_TYPES_SELECTION,
        string='MyDATA Invoice Type',
        default='1.1',
    )
    l10n_gr_edi_available_inv_type = fields.Char(compute='_compute_l10n_gr_edi_available_inv_type')
    l10n_gr_edi_correlation_id = fields.Many2one(
        comodel_name='account.move',
        string='MyDATA Correlated Invoice',
        domain="[('l10n_gr_edi_mark', '!=', False), ('move_type', '=', move_type)]",
    )
    l10n_gr_edi_need_correlated = fields.Boolean(compute='_compute_l10n_gr_edi_need_correlated')
    l10n_gr_edi_document_ids = fields.One2many(
        comodel_name='mydata.document',
        inverse_name='move_id',
        copy=False,
        readonly=True,
    )
    l10n_gr_edi_active_document_id = fields.Many2one('mydata.document')

    @api.onchange('l10n_gr_edi_inv_type')
    def _onchange_l10n_gr_edi_inv_type(self):
        for move in self:
            move.l10n_gr_edi_correlation_id = False
            move.invoice_line_ids.l10n_gr_edi_detail_type = False
            move.invoice_line_ids.l10n_gr_edi_cls_vat = False
            for line in move.invoice_line_ids:
                line._l10n_gr_edi_update_preferred_classification()

    @api.depends('move_type')
    def _compute_l10n_gr_edi_available_inv_type(self):
        for move in self:
            if move.move_type in ('out_invoice', 'out_refund'):
                move.l10n_gr_edi_available_inv_type = ','.join(INVOICE_TYPES_HAVE_INCOME)
            else:
                move.l10n_gr_edi_available_inv_type = ','.join(INVOICE_TYPES_HAVE_EXPENSE)

    @api.depends('l10n_gr_edi_inv_type')
    def _compute_l10n_gr_edi_need_correlated(self):
        for move in self:
            move.l10n_gr_edi_need_correlated = move.l10n_gr_edi_inv_type in TYPES_WITH_CORRELATE_INVOICE

    def mydata_prepare_constraints(self):
        """ Tries to catch all possible errors before sending to MyDATA API """
        self.ensure_one()
        errors = []

        if not self.company_id.l10n_gr_edi_aade_id or not self.company_id.l10n_gr_edi_aade_key:
            errors.append(_('You need to set AADE ID and Key in the company settings.'))
        if not self.l10n_gr_edi_inv_type:
            errors.append(_('Missing MyDATA Invoice Type'))
        if not self.partner_id.vat:
            errors.append(_('Missing VAT on partner %s', self.partner_id.name))
        if not self.company_id.vat:
            errors.append(_('Missing VAT on company %s', self.company_id.name))

        for line in self.invoice_line_ids:
            if not line.l10n_gr_edi_cls_category and line.l10n_gr_edi_available_cls_category:
                errors.append(_('Missing MyDATA classification category on line %s', line.name))
            if not line.l10n_gr_edi_cls_type \
                    and line.l10n_gr_edi_available_cls_type \
                    and (line.move_id.l10n_gr_edi_inv_type, line.l10n_gr_edi_cls_category) \
                    not in COMBINATIONS_WITH_POSSIBLE_EMPTY_TYPE:
                errors.append(_('Missing MyDATA classification type on line %s', line.name))
            if len(line.tax_ids) > 1:
                errors.append(_('MyDATA does not support multiple taxes on line %s', line.name))
            if not line.tax_ids:
                errors.append(_('Missing tax on line %s', line.name))
            if len(line.tax_ids) == 1 and line.tax_ids.amount == 0 and not line.l10n_gr_edi_tax_exemption_category:
                errors.append(_('MyDATA Tax Exemption Category is missing for line %s', line.name))
            if len(line.tax_ids) == 1 and line.tax_ids.amount not in VALID_TAX_AMOUNTS:
                errors.append(_('Invalid tax amount for line %s. The valid values are %s',
                                line.name, ', '.join(str(tax) for tax in VALID_TAX_AMOUNTS)))

        if errors:
            self.env['mydata.document'].create([{
                'move_id': self.id,
                'state': 'error',
                'message': '\n'.join(errors),
                'datetime': fields.Datetime.now(),
            }])
        return errors

    @staticmethod
    def _get_mydata_issuer_counterpart_vals(move):
        party_vals = {
            'issuer_vat': move.company_id.vat,
            'issuer_country': move.company_id.country_code,
            'issuer_branch': len(move.company_id.parent_ids - move.company_id),
        }

        if move.country_code != 'GR':  # issuer not from Greece requires name & address
            party_vals.update({
                'issuer_name': move.company_id.name.encode('utf-8'),
                'issuer_postal_code': move.company_id.zip,
                'issuer_city': move.company_id.city.encode('utf-8'),
            })

        if move.l10n_gr_edi_inv_type not in TYPES_WITH_FORBIDDEN_COUNTERPART:  # some inv_type disallow counterpart
            counterpart_vat = move.partner_id.vat
            party_vals.update({
                'counterpart_vat': counterpart_vat,
                'counterpart_country': move.partner_id.country_code,
                'counterpart_branch': len(move.partner_id.company_id.parent_ids - move.partner_id.company_id),
            })
            if move.partner_id.country_code != 'GR':  # counterpart not from Greece (requires name & address)
                party_vals.update({
                    'counterpart_name': move.partner_id.name.encode('utf-8'),
                    'counterpart_postal_code': move.partner_id.zip,
                    'counterpart_city': move.partner_id.city.encode('utf-8'),
                })

        return party_vals

    @staticmethod
    def _get_mydata_payment_method_vals(move):
        payment_vals = {'payment_details': []}
        reconciled_lines = move.line_ids.filtered(
            lambda line: line.account_id.account_type in ('asset_receivable', 'liability_payable'))

        for apr in reconciled_lines.matched_credit_ids:  # for Customer Invoices payment
            payment_vals['payment_details'].append({
                'type': apr.credit_move_id.payment_id.payment_method_line_id.l10n_gr_edi_payment_method_id or '1',
                'amount': apr.debit_amount_currency,
            })
        for apr in reconciled_lines.matched_debit_ids:  # for Credit Notes payment
            payment_vals['payment_details'].append({
                'type': apr.debit_move_id.payment_id.payment_method_line_id.l10n_gr_edi_payment_method_id or '1',
                'amount': apr.credit_amount_currency,
            })

        return payment_vals

    @staticmethod
    def _get_mydata_vat_category_vals(line):
        vat_vals = {'vat_category': 7, 'vat_exemption_category': ''}

        if line.tax_ids and line.move_id.l10n_gr_edi_inv_type not in TYPES_WITH_VAT_EXEMPT:
            vat_vals['vat_category'] = {24: 1, 13: 2, 6: 3, 17: 4, 9: 5, 4: 6, 0: 7}[int(line.tax_ids.amount)]

        if vat_vals['vat_category'] == 7 and line.move_id.l10n_gr_edi_inv_type in TYPES_WITH_VAT_CATEGORY_8:
            vat_vals['vat_category'] = 8

        if vat_vals['vat_category'] == 7:
            # need vat exemption category
            vat_vals['vat_exemption_category'] = line.l10n_gr_edi_tax_exemption_category

        return vat_vals

    @staticmethod
    def _get_mydata_classification_vals(line):
        cls_vals = {'ecls': [], 'icls': []}

        if line.l10n_gr_edi_cls_category:
            cls_vals_list = cls_vals['ecls'] if line.l10n_gr_edi_cls_category in CLASSIFICATION_CATEGORY_EXPENSE else cls_vals['icls']
            cls_type = line.l10n_gr_edi_cls_type or ''
            if len(cls_type) > 0 and cls_type[0] == 'X':  # handle duplicate E3 type on inv type 17.5
                cls_type = cls_type[1:]

            cls_vals_list.append({
                'category': line.l10n_gr_edi_cls_category,
                'type': cls_type,
                'amount': abs(line.balance),
            })

            if line.l10n_gr_edi_cls_vat:
                cls_vals_list.append({
                    'category': '',
                    'type': line.l10n_gr_edi_cls_vat,
                    'amount': abs(line.balance),
                })

        return cls_vals

    @staticmethod
    def _get_mydata_sum_classification_vals(details):
        icls_vals, ecls_vals = {}, {}
        summary_icls, summary_ecls = [], []

        for detail in details:
            icls_list, ecls_list = detail['icls'], detail['ecls']
            for icls in icls_list:
                category_type = (icls['category'], icls['type'])
                icls_vals.setdefault(category_type, 0)
                icls_vals[category_type] += icls['amount']
            for ecls in ecls_list:
                category_type = (ecls['category'], ecls['type'])
                ecls_vals.setdefault(category_type, 0)
                ecls_vals[category_type] += ecls['amount']

        for category_type, amount in icls_vals.items():
            category, cls_type = category_type
            summary_icls.append({'type': cls_type, 'category': category, 'amount': amount})
        for category_type, amount in ecls_vals.items():
            category, cls_type = category_type
            summary_ecls.append({'type': cls_type, 'category': category, 'amount': amount})

        return {'summary_icls': summary_icls, 'summary_ecls': summary_ecls}

    @staticmethod
    def _cleanup_xml_value(xml_value):
        """ Remove empty string and list value from xml_vals """
        if isinstance(xml_value, list):
            return [AccountMove._cleanup_xml_value(item) for item in xml_value if item not in ('', [])]
        elif isinstance(xml_value, dict):
            return {k: AccountMove._cleanup_xml_value(v) for k, v in xml_value.items() if v not in ('', [])}
        else:
            return xml_value

    def _prepare_mydata_invoice_xml_vals(self):
        xml_vals = {'invoices': []}

        for move in self:
            details = []
            for line in move.line_ids.filtered(lambda l: l.display_type == 'product'):
                details.append({
                    'line_number': len(details) + 1,
                    'detail_type': line.l10n_gr_edi_detail_type or '',
                    'net_value': abs(line.balance),
                    'vat_amount': round(line.price_total - line.price_subtotal, 2),
                    **self._get_mydata_vat_category_vals(line),
                    **self._get_mydata_classification_vals(line),
                })

            xml_vals['invoices'].append({
                'header_series': '_'.join(move.name.split('/')[:-1]),
                'header_aa': move.name.split('/')[-1],
                'header_issue_date': move.date.isoformat(),
                'header_invoice_type': move.l10n_gr_edi_inv_type,
                'header_currency': move.currency_id.name,
                'header_correlate': move.l10n_gr_edi_correlation_id.l10n_gr_edi_mark or '',
                'details': details,
                'summary_total_net_value': move.amount_untaxed,
                'summary_total_vat_amount': move.amount_tax,
                'summary_total_withheld_amount': 0,
                'summary_total_fees_amount': 0,
                'summary_total_stamp_duty_amount': 0,
                'summary_total_other_taxes_amount': 0,
                'summary_total_deductions_amount': 0,
                'summary_total_gross_value': move.amount_total,
                **self._get_mydata_issuer_counterpart_vals(move),
                **self._get_mydata_payment_method_vals(move),
                **self._get_mydata_sum_classification_vals(details),
            })

        xml_vals = self._cleanup_xml_value(xml_vals)
        return xml_vals

    def _prepare_mydata_classification_xml_vals(self):
        xml_vals = {'invoices': []}

        for move in self:
            details = []
            for line in move.line_ids.filtered(lambda l: l.display_type == 'product'):
                details.append({
                    'line_number': len(details) + 1,
                    **self._get_mydata_classification_vals(line),
                })

            xml_vals['invoices'].append({
                'mark': move.l10n_gr_edi_mark,
                'transaction_mode': '',  # todo - add way to 'reject' received invoices
                'details': details,
            })

        xml_vals = self._cleanup_xml_value(xml_vals)
        return xml_vals

    def mydata_send_invoices(self):
        """ Create Document(s) of XML values from selected invoice(s) and send them to MyDATA """
        xml_vals = self._prepare_mydata_invoice_xml_vals()
        document_ids = self.env['mydata.document'].create([{'move_id': move.id} for move in self])
        document_ids._send_mydata_invoices_xml(xml_vals)

    def mydata_send_expense_classifications(self):
        """ Create XML documents for Expense Classifications and send them to MyDATA """
        xml_vals = self._prepare_mydata_classification_xml_vals()
        document_ids = self.env['mydata.document'].create([{'move_id': move.id} for move in self])
        document_ids._send_mydata_expense_classifications_xml(xml_vals)

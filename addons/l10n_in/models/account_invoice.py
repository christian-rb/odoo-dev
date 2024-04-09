# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
import re

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from odoo.tools.image import image_data_uri


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_in_gst_treatment = fields.Selection([
            ('regular', 'Registered Business - Regular'),
            ('composition', 'Registered Business - Composition'),
            ('unregistered', 'Unregistered Business'),
            ('consumer', 'Consumer'),
            ('overseas', 'Overseas'),
            ('special_economic_zone', 'Special Economic Zone'),
            ('deemed_export', 'Deemed Export'),
            ('uin_holders', 'UIN Holders'),
        ], string="GST Treatment", compute="_compute_l10n_in_gst_treatment", store=True, readonly=False, copy=True)
    l10n_in_state_id = fields.Many2one('res.country.state', string="Place of supply", compute="_compute_l10n_in_state_id", store=True, readonly=False)
    l10n_in_gstin = fields.Char(string="GSTIN")
    # For Export invoice this data is need in GSTR report
    l10n_in_shipping_bill_number = fields.Char('Shipping bill number')
    l10n_in_shipping_bill_date = fields.Date('Shipping bill date')
    l10n_in_shipping_port_code_id = fields.Many2one('l10n_in.port.code', 'Port code')
    l10n_in_reseller_partner_id = fields.Many2one('res.partner', 'Reseller', domain=[('vat', '!=', False)], help="Only Registered Reseller")
    l10n_in_journal_type = fields.Selection(string="Journal Type", related='journal_id.type')
    l10n_in_tcs_tds_warning = fields.Char('TDC/TCS Warning', compute="_compute_l10n_in_tcs_tds_warning", store=True)

    @api.depends('partner_id', 'partner_id.l10n_in_gst_treatment', 'state')
    def _compute_l10n_in_gst_treatment(self):
        indian_invoice = self.filtered(lambda m: m.country_code == 'IN')
        for record in indian_invoice:
            if record.state == 'draft':
                gst_treatment = record.partner_id.l10n_in_gst_treatment
                if not gst_treatment:
                    gst_treatment = 'unregistered'
                    if record.partner_id.country_id.code == 'IN' and record.partner_id.vat:
                        gst_treatment = 'regular'
                    elif record.partner_id.country_id and record.partner_id.country_id.code != 'IN':
                        gst_treatment = 'overseas'
                record.l10n_in_gst_treatment = gst_treatment
        (self - indian_invoice).l10n_in_gst_treatment = False

    @api.depends('partner_id', 'company_id')
    def _compute_l10n_in_state_id(self):
        for move in self:
            if move.country_code == 'IN' and move.journal_id.type == 'sale':
                country_code = move.partner_id.country_id.code
                if country_code == 'IN':
                    move.l10n_in_state_id = move.partner_id.state_id
                elif country_code:
                    move.l10n_in_state_id = self.env.ref('l10n_in.state_in_oc', raise_if_not_found=False)
                else:
                    move.l10n_in_state_id = move.company_id.state_id
            elif move.country_code == 'IN' and move.journal_id.type == 'purchase':
                move.l10n_in_state_id = move.company_id.state_id
            else:
                move.l10n_in_state_id = False

    @api.depends('state')
    def _compute_l10n_in_tcs_tds_warning(self):
        for move in self:
            if move.state == 'posted':
                warning_sections = []
                partner_pan = move.partner_id.l10n_in_pan
                company_pan = move.company_id.l10n_in_pan
                per_transection_obj = self._l10n_in_calculate_per_transection_object()
                aggregate_obj = self._l10n_in_calculate_aggregate_total(partner_pan, company_pan)

                if per_transection_obj or aggregate_obj:
                    # check if per teansection limit is exceeded or not
                    for tax_group_id in per_transection_obj:
                        if tax_group_id.l10n_in_is_per_transection_limit and per_transection_obj[tax_group_id] > tax_group_id.l10n_in_per_transection_limit:
                            warning_sections.append(tax_group_id.name[5:])
                    # check if aggregate limit is exceeded or not
                    for tax_group_id in aggregate_obj:
                        if any(tax_group_id in line.account_id.l10n_in_tds_tcs_section for line in move.invoice_line_ids):
                            if tax_group_id.l10n_in_is_aggregate_limit and aggregate_obj[tax_group_id] > tax_group_id.l10n_in_aggregate_limit and tax_group_id.name[5:] not in warning_sections:
                                warning_sections.append(tax_group_id.name[5:])
                    warning = ', '.join(warning_sections)

                    if move.journal_id.type == 'sale':
                        warning_message = _("It's advisable to collect TCS u/s %s on this transaction.") % warning
                    elif move.journal_id.type == 'purchase':
                        warning_message = _("It's advisable to deduct TDS u/s %s on this transaction.") % warning
                    move.l10n_in_tcs_tds_warning = len(warning_sections) > 0 and warning_message or False
                    if not move.invoice_line_ids.filtered(lambda line: line.account_id.l10n_in_tds_tcs_section not in line.tax_ids.mapped('tax_group_id')):
                        move.l10n_in_tcs_tds_warning = False
                else:
                    move.l10n_in_tcs_tds_warning = False

    @api.onchange('name')
    def _onchange_name_warning(self):
        if self.country_code == 'IN' and self.journal_id.type == 'sale' and self.name and (len(self.name) > 16 or not re.match(r'^[a-zA-Z0-9-\/]+$', self.name)):
            return {'warning': {
                'title' : _("Invalid sequence as per GST rule 46(b)"),
                'message': _(
                    "The invoice number should not exceed 16 characters\n"
                    "and must only contain '-' (hyphen) and '/' (slash) as special characters"
                )
            }}
        return super()._onchange_name_warning()

    def action_show_invoice_lines_tds(self):
        self.ensure_one()
        lines = self.invoice_line_ids.filtered(lambda line: line.account_id.l10n_in_tds_tcs_section not in line.tax_ids.mapped('tax_group_id'))
        view_id = self.env.ref('l10n_in.view_move_line_tree_tcs_tds_l10n_in').id
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Invoice Lines',
            'view_mode': 'list',
            'views': [[view_id, 'list']],
            'res_model': 'account.move.line',
            'domain': [('id', 'in', lines.ids)],
        }
        return action

    def _l10n_in_calculate_aggregate_total(self, partner_pan, company_pan):
        company = self.env.company
        fiscal_year_last_day = company.fiscalyear_last_day
        fiscal_year_last_month = company.fiscalyear_last_month
        current_year = fields.Date.today().year
        fiscal_year_end_date = fields.Date.from_string('%s-%s-%s' % (current_year + 1, fiscal_year_last_month, fiscal_year_last_day))
        fiscal_year_start_date = fields.Date.add(fields.Date.subtract(fiscal_year_end_date, months=12), days=1)

        parent_company_id = self.env.company.parent_id.id or self.env.company.id
        company_ids = self.env['res.company'].search(['|', '|', ('id', 'child_of', parent_company_id), ('id', '=', parent_company_id), ('l10n_in_pan', '=', company_pan)])
        partner_ids = self.env['res.partner'].search([('l10n_in_pan', '=', partner_pan)])
        moves_within_fiscal_year = self.env['account.move'].search([
            ('date', '>=', fiscal_year_start_date),
            ('date', '<=', fiscal_year_end_date),
            ('partner_id', 'in', partner_ids.ids),
            ('company_id', 'in', company_ids.ids),
        ])
        aggregate_obj = self._l10n_in_calculate_aggregate_object(moves_within_fiscal_year)
        return aggregate_obj

    def _l10n_in_calculate_per_transection_object(self):
        for move in self:
            accounts = set(move.invoice_line_ids.mapped('account_id'))
            per_transection_obj = {account.l10n_in_tds_tcs_section: 0 for account in accounts}
            if per_transection_obj:
                for line in move.invoice_line_ids:
                    if line.account_id.l10n_in_tds_tcs_section not in line.tax_ids.mapped('tax_group_id'):
                        tax_group_id = line.account_id.l10n_in_tds_tcs_section
                        per_transection_obj[tax_group_id] += line.price_total if tax_group_id.l10n_in_consider_tax == 'total_amount' else line.price_subtotal
            else:
                return False
        return per_transection_obj

    def _l10n_in_calculate_aggregate_object(self, moves):
        aggregate_obj = {}
        for move in moves:
            accounts = set(move.invoice_line_ids.mapped('account_id'))
            for account in accounts:
                if account.l10n_in_tds_tcs_section not in aggregate_obj:
                    aggregate_obj[account.l10n_in_tds_tcs_section] = 0
                else:
                    continue
            if aggregate_obj:
                for line in move.invoice_line_ids:
                    if line.account_id.l10n_in_tds_tcs_section not in line.tax_ids.mapped('tax_group_id'):
                        tax_group_id = line.account_id.l10n_in_tds_tcs_section
                        aggregate_obj[tax_group_id] += line.price_total if tax_group_id.l10n_in_consider_tax == 'total_amount' else line.price_subtotal
        return aggregate_obj

    def _get_name_invoice_report(self):
        self.ensure_one()
        if self.country_code == 'IN':
            return 'l10n_in.l10n_in_report_invoice_document_inherit'
        return super()._get_name_invoice_report()

    def _post(self, soft=True):
        """Use journal type to define document type because not miss state in any entry including POS entry"""
        posted = super()._post(soft)
        gst_treatment_name_mapping = {k: v for k, v in
                             self._fields['l10n_in_gst_treatment']._description_selection(self.env)}
        for move in posted.filtered(lambda m: m.country_code == 'IN' and m.is_sale_document()):
            if move.l10n_in_state_id and not move.l10n_in_state_id.l10n_in_tin:
                raise UserError(_("Please set a valid TIN Number on the Place of Supply %s", move.l10n_in_state_id.name))
            if not move.company_id.state_id:
                msg = _("Your company %s needs to have a correct address in order to validate this invoice.\n"
                "Set the address of your company (Don't forget the State field)", move.company_id.name)
                action = {
                    "view_mode": "form",
                    "res_model": "res.company",
                    "type": "ir.actions.act_window",
                    "res_id" : move.company_id.id,
                    "views": [[self.env.ref("base.view_company_form").id, "form"]],
                }
                raise RedirectWarning(msg, action, _('Go to Company configuration'))
            move.l10n_in_gstin = move.partner_id.vat
            if not move.l10n_in_gstin and move.l10n_in_gst_treatment in ['regular', 'composition', 'special_economic_zone', 'deemed_export']:
                raise ValidationError(_(
                    "Partner %(partner_name)s (%(partner_id)s) GSTIN is required under GST Treatment %(name)s",
                    partner_name=move.partner_id.name,
                    partner_id=move.partner_id.id,
                    name=gst_treatment_name_mapping.get(move.l10n_in_gst_treatment)
                ))
        return posted

    def _l10n_in_get_warehouse_address(self):
        """Return address where goods are delivered/received for Invoice/Bill"""
        # TO OVERRIDE
        self.ensure_one()
        return False

    def _generate_qr_code(self, silent_errors=False):
        self.ensure_one()
        if self.company_id.country_code == 'IN':
            payment_url = 'upi://pay?pa=%s&pn=%s&am=%s&tr=%s&tn=%s' % (
                self.company_id.l10n_in_upi_id,
                self.company_id.name,
                self.amount_residual,
                self.payment_reference or self.name,
                ("Payment for %s" % self.name))
            barcode = self.env['ir.actions.report'].barcode(barcode_type="QR", value=payment_url, width=120, height=120)
            return image_data_uri(base64.b64encode(barcode))
        return super()._generate_qr_code(silent_errors)

    def _l10n_in_get_hsn_summary_table(self):
        self.ensure_one()
        display_uom = self.env.user.has_group('uom.group_uom')

        base_lines = []
        for line in self.invoice_line_ids.filtered(lambda x: x.display_type == 'product'):
            taxes_data = line.tax_ids._convert_to_dict_for_taxes_computation()
            product_values = self.env['account.tax']._eval_taxes_computation_turn_to_product_values(
                taxes_data,
                product=line.product_id,
            )

            base_lines.append({
                'l10n_in_hsn_code': line.l10n_in_hsn_code,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
                'product_values': product_values,
                'uom': {'id': line.product_uom_id.id, 'name': line.product_uom_id.name},
                'taxes_data': taxes_data,
            })
        return self.env['account.tax']._l10n_in_get_hsn_summary_table(base_lines, display_uom)

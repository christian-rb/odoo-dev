# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons.iap import jsonrpc
from odoo.exceptions import UserError, AccessError

TEST_GST_NUMBER = "36AABCT1332L011"

class ResPartner(models.Model):
    _inherit = 'res.partner'

    l10n_in_gst_treatment = fields.Selection([
            ('regular', 'Registered Business - Regular'),
            ('composition', 'Registered Business - Composition'),
            ('unregistered', 'Unregistered Business'),
            ('consumer', 'Consumer'),
            ('overseas', 'Overseas'),
            ('special_economic_zone', 'Special Economic Zone'),
            ('deemed_export', 'Deemed Export'),
            ('uin_holders', 'UIN Holders'),
        ], string="GST Treatment")

    l10n_in_pan = fields.Char(
        string="PAN",
        help="PAN enables the department to link all transactions of the person with the department.\n"
             "These transactions include taxpayments, TDS/TCS credits, returns of income/wealth/gift/FBT,"
             " specified transactions, correspondence, and so on.\n"
             "Thus, PAN acts as an identifier for the person with the tax department."
    )

    l10n_in_gstin_verified_status = fields.Char(string="GSTIN Verified Status")
    l10n_in_gstin_verified_date = fields.Date(string="GSTIN Verified Date")
    l10n_in_gstin_status_api_service = fields.Boolean(compute='_compute_l10n_in_gstin_status_api_service')
    display_pan_warning = fields.Boolean(string="Display pan warning", compute="_compute_display_pan_warning")

    @api.depends('l10n_in_pan')
    def _compute_display_pan_warning(self):
        self.display_pan_warning = self.vat and self.l10n_in_pan and self.l10n_in_pan != self.vat[2:12]

    def _compute_l10n_in_gstin_status_api_service(self):
        gstin_api_status = self.env['ir.config_parameter'].sudo().get_param('l10n_in.gstin_status_api_service', default=False)
        self.l10n_in_gstin_status_api_service = gstin_api_status

    @api.onchange('company_type')
    def onchange_company_type(self):
        res = super().onchange_company_type()
        if self.country_id and self.country_id.code == 'IN':
            self.l10n_in_gst_treatment = (self.company_type == 'company') and 'regular' or 'consumer'
        return res

    @api.onchange('country_id')
    def _onchange_country_id(self):
        res = super()._onchange_country_id()
        if self.country_id and self.country_id.code != 'IN':
            self.l10n_in_gst_treatment = 'overseas'
        elif self.country_id and self.country_id.code == 'IN':
            self.l10n_in_gst_treatment = (self.company_type == 'company') and 'regular' or 'consumer'
        return res

    @api.onchange('vat')
    def onchange_vat(self):
        if self.vat and self.check_vat_in(self.vat):
            state_id = self.env['res.country.state'].search([('l10n_in_tin', '=', self.vat[:2])], limit=1)
            if state_id:
                self.state_id = state_id
            if self.vat[2].isalpha():
                self.l10n_in_pan = self.vat[2:12]

    @api.model
    def _commercial_fields(self):
        res = super()._commercial_fields()
        return res + ['l10n_in_gst_treatment', 'l10n_in_pan']

    def check_vat_in(self, vat):
        """
            This TEST_GST_NUMBER is used as test credentials for EDI
            but this is not a valid number as per the regular expression
            so TEST_GST_NUMBER is considered always valid
        """
        if vat == TEST_GST_NUMBER:
            return True
        return super().check_vat_in(vat)

    def get_verified_status(self):
        if not self.vat:
            raise UserError(_('Enter GSTIN before checking the status.'))

        url = "https://jva-odoo-iap-apps-15-0-12609655.dev.odoo.com/iap/l10n_in_reports/1/public/search"
        user_token = self.env["iap.account"].get("l10n_in_edi")
        uuid = self.env["ir.config_parameter"].sudo().get_param("database.uuid")
        for partner in self:
            params = {"account_token": user_token.account_token, "dbuuid": uuid, "gstin_to_search": partner.vat}
            try:
                response = jsonrpc(url, params=params, timeout=25)
                if response.get('error'):
                    error_data = response['error'][0]
                    raise UserError(_("Error: %s", str(error_data['message'])))
            except AccessError as e:
                raise UserError(_("Error: %s", str(e)))
            verified_status = response.get('data', {}).get('sts', "")
            if verified_status:
                partner.l10n_in_gstin_verified_status = verified_status
            if partner.l10n_in_gstin_verified_status:
                partner.l10n_in_gstin_verified_date = fields.Date.today()

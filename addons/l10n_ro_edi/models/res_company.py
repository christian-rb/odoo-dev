# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models
from werkzeug.urls import url_join


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_ro_edi_client_id = fields.Char('Client ID')
    l10n_ro_edi_client_secret = fields.Char('Client Secret')
    l10n_ro_edi_access_token = fields.Char('Access Token')
    l10n_ro_edi_refresh_token = fields.Char('Refresh Token')
    l10n_ro_edi_access_expiry_date = fields.Date('Access Token Expiry Date')
    l10n_ro_edi_refresh_expiry_date = fields.Date('Refresh Token Expiry Date')
    l10n_ro_edi_callback_url = fields.Char(compute='_compute_l10n_ro_edi_callback_url')
    l10n_ro_edi_test_env = fields.Boolean('Use Test Environment', default=True)
    l10n_ro_edi_oauth_error = fields.Char()

    def _compute_l10n_ro_edi_callback_url(self):
        for company in self:
            company.l10n_ro_edi_callback_url = url_join(self.get_base_url(), 'l10n_ro_edi/callback/%s' % company.id)

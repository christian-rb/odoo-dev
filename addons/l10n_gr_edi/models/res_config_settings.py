# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    l10n_gr_aade_user_id = fields.Char(related='company_id.l10n_gr_aade_user_id', readonly=False)
    l10n_gr_subscription_key = fields.Char(related='company_id.l10n_gr_subscription_key', readonly=False)
    l10n_gr_edi_test_env = fields.Boolean(related='company_id.l10n_gr_edi_test_env', readonly=False)
    l10n_gr_edi_test_id = fields.Char(related='company_id.l10n_gr_edi_test_id', readonly=False)
    l10n_gr_edi_test_vat = fields.Char(related='company_id.l10n_gr_edi_test_vat', readonly=False)
    l10n_gr_edi_test_key = fields.Char(related='company_id.l10n_gr_edi_test_key', readonly=False)

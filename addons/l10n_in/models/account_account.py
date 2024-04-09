from odoo import fields, models


class AccountAccount(models.Model):
    _inherit = 'account.account'

    country_code = fields.Char(related="company_id.country_id.code")
    l10n_in_tds_tcs_section = fields.Many2one('account.tax.group', string="TCS/TDS Section", domain="[('l10n_in_tax_group', 'in', ['TDS', 'TCS'])]")

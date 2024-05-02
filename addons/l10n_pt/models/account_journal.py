from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    l10n_pt_at_series_invoice_id = fields.Many2one("l10n_pt.at.series", string="Official Autoridade Tributária (AT) Series for Invoices")
    l10n_pt_at_series_refund_id = fields.Many2one("l10n_pt.at.series", string="Official Autoridade Tributária (AT) Series for Refunds")

    def _prepare_liquidity_account_vals(self, company, code, vals):
        account_vals = super()._prepare_liquidity_account_vals(company, code, vals)
        if company.account_fiscal_country_id.code == 'PT':
            if vals.get('type') == 'cash':
                account_vals['l10n_pt_taxonomy_code'] = 1
            elif vals.get('type') == 'bank':
                account_vals['l10n_pt_taxonomy_code'] = 2
        return account_vals

    @api.constrains('type', 'restrict_mode_hash_table')
    def _check_journal_restrict_mode(self):
        for journal in self:
            if (
                journal.company_id.account_fiscal_country_id.code == 'PT'
                and journal.type == 'sale'
                and not journal.restrict_mode_hash_table
            ):
                raise ValidationError(_("The 'Lock Posted Entries with Hash' option must be enabled for Portuguese sale journals."))

    def write(self, vals):
        res = super().write(vals)
        for journal in self:
            if (
                (vals.get('l10n_pt_at_series_invoice_id') and journal.l10n_pt_at_series_invoice_id)
                or
                (vals.get('l10n_pt_at_series_refund_id') and journal.l10n_pt_at_series_refund_id)
            ):
                if self.env['account.move'].search_count([('journal_id', '=', journal.id), ('inalterable_hash', '!=', False)]):
                    raise UserError(_("You cannot change the Autoridade Tributária (AT) series of a journal once it has been used."))
        return res

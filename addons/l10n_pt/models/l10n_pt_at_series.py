from odoo import models, fields, _, api
from odoo.exceptions import UserError


class L10nPtATSeries(models.Model):
    _name = "l10n_pt.at.series"
    _description = "Official Series for the Autoridade Tributária (AT)"
    _check_company_auto = True
    _check_company_domain = models.check_company_domain_parent_of
    _rec_name = 'code'

    code = fields.Char("Code of the series", required=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    date_end = fields.Date()
    active = fields.Boolean(compute='_compute_active', search='_search_active')

    _sql_constraints = [('code', 'unique(code)', 'Code must be unique.')]

    def _compute_active(self):
        for at_series in self:
            at_series.active =  at_series.date_end >= fields.Date.today() if at_series.date_end else True

    def _get_code(self):
        self.ensure_one()
        if not self.active:
            raise UserError(_("The series %s is not active.") % self.code)
        return self.code

    def _search_active(self, operator, value):
        if operator not in ['in', '=', '!=']:
            raise ValueError(_('This operator is not supported'))
        now = fields.Datetime.now()
        if (operator == '=' and value) or (operator == '!=' and not value):
            domain = ['|', ('date_end', '=', False), ('date_end', '>=', now)]
        else:
            domain = ['|', ('date_end', '=', False), ('date_end', '<', now)]
        return domain

    def write(self, vals):
        res = super().write(vals)
        if vals.get('code'):
            raise UserError(_("You cannot change the code of a series."))
        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_except_used(self):
        if (
            self.env['account.journal'].search_count([('l10n_pt_at_series_invoice_id', 'in', self.ids)])
            or self.env['account.journal'].search_count([('l10n_pt_at_series_refund_id', 'in', self.ids)])
        ):
            raise UserError(_("You cannot delete a series that is used in a journal."))
        return super().unlink()

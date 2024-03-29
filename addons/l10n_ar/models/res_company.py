# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class ResCompany(models.Model):

    _inherit = "res.company"

    l10n_ar_gross_income_number = fields.Char(
        related='partner_id.l10n_ar_gross_income_number', string='Gross Income Number', readonly=False,
        help="This field is required in order to print the invoice report properly")
    l10n_ar_gross_income_type = fields.Selection(
        related='partner_id.l10n_ar_gross_income_type', string='Gross Income', readonly=False,
        help="This field is required in order to print the invoice report properly")
    l10n_ar_afip_responsibility_type_id = fields.Many2one(
        domain="[('code', 'in', [1, 4, 6])]", related='partner_id.l10n_ar_afip_responsibility_type_id', readonly=False)
    l10n_ar_company_requires_vat = fields.Boolean(compute='_compute_l10n_ar_company_requires_vat', string='Company Requires Vat?')
    l10n_ar_afip_start_date = fields.Date('Activities Start')

    @api.model
    def _get_ar_responsibility_match(self):
        """ return responsibility type that match with the given chart_template code
        """
        return {
            'ar_base': self.env.ref('l10n_ar.res_RM'),
            'ar_ex': self.env.ref('l10n_ar.res_IVAE'),
            'ar_ri': self.env.ref('l10n_ar.res_IVARI'),
        }

    def setup_ar_company_if_ar_coa(self):
        """ Set companies AFIP Responsibility and Country if AR CoA is installed, also set tax calculation rounding
        method required in order to properly validate match AFIP invoices.

        Also, raise a warning if the user is trying to install a CoA that does not match with the defined AFIP
        Responsibility defined in the company
        """
        coa_responsibility = self._get_ar_responsibility_match()
        for company in self.filtered(lambda c: coa_responsibility.get(c.chart_template)):
            company.write({
                'l10n_ar_afip_responsibility_type_id': coa_responsibility.get(company.chart_template).id,
                'tax_calculation_rounding_method': 'round_globally',
                'country_id': self.env.ref('base.ar').id,
            })

            # set CUIT identification type `which is the argentinean vat` in the created company partner instead of
            # the default VAT type.
            company.partner_id.l10n_latam_identification_type_id = self.env.ref('l10n_ar.it_cuit')

    def create(self, vals):
        companies = super().create(vals)
        companies.setup_ar_company_if_ar_coa()
        return companies

    def write(self, vals):
        res = super().write(vals)
        if 'chart_template' in vals:
            self.setup_ar_company_if_ar_coa()
        return res

    @api.depends('l10n_ar_afip_responsibility_type_id')
    def _compute_l10n_ar_company_requires_vat(self):
        recs_requires_vat = self.filtered(lambda x: x.l10n_ar_afip_responsibility_type_id.code == '1')
        recs_requires_vat.l10n_ar_company_requires_vat = True
        remaining = self - recs_requires_vat
        remaining.l10n_ar_company_requires_vat = False

    def _localization_use_documents(self):
        """ Argentinean localization use documents """
        self.ensure_one()
        return self.account_fiscal_country_id.code == "AR" or super()._localization_use_documents()

    @api.constrains('l10n_ar_afip_responsibility_type_id')
    def _check_accounting_info(self):
        """ Do not let to change the AFIP Responsibility of the company if there is already installed a chart of
        account and if there has accounting entries """
        if self._existing_accounting():
            raise ValidationError(_(
                'Could not change the AFIP Responsibility of this company because there are already accounting entries.'))

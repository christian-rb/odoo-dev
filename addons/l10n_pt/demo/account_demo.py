# -*- coding: utf-8 -*-
from odoo import api, models


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @api.model
    def _get_demo_data(self, company=False):
        demo_data = super()._get_demo_data(company)
        if company.account_fiscal_country_id.code == "PT":
            sale_journals = self.env['account.journal'].search([('type', '=', 'sale'), ('company_id', '=', company.id)])
            sale_journals.l10n_pt_at_series_invoice_id = self.env['l10n_pt.at.series'].create({
                'code': f'DEMO_INVOICE_SERIES{company.id}',
                'company_id': company.id,
            })
            sale_journals.l10n_pt_at_series_refund_id = self.env['l10n_pt.at.series'].create({
                'code': f'DEMO_REFUND_SERIES{company.id}',
                'company_id': company.id,
            })
        return demo_data

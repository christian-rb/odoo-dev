# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _

class AccountChartTemplate(models.AbstractModel):
    _inherit = 'account.chart.template'


    def _load(self, template_code, company, install_demo):
        res = super()._load(template_code, company, install_demo)
        # If Responsable Monotributista remove the default purchase tax
        if template_code in ('ar_base', 'ar_ex'):
            company.account_purchase_tax_id = self.env['account.tax']
        return res

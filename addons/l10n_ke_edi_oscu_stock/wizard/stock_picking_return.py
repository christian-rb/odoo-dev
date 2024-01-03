# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, models
from odoo.exceptions import UserError


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def create_returns(self):
        for wizard in self:
            if wizard.company_id.account_fiscal_country_id.code == 'KE':
                if any(not l.to_refund for l in wizard.product_return_moves):
                    raise UserError(_('You need to check To Refund to align invoices and transfers. '))
        return super().create_returns()

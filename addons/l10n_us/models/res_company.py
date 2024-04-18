# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    show_taxes = fields.Boolean(compute='_set_show_taxes', store=False, default=True)

    def _set_show_taxes(self):
        for record in self:
            record.show_taxes = self.country_code != 'US'

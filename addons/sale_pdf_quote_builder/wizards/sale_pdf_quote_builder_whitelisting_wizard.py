# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models


class SalePDFQuoteBuilderWhitelistingWizard(models.TransientModel):
    _name = 'sale.pdf.quote.builder.whitelisting.wizard'
    _description = "Sale PDF Quote Builder Whitelisting Wizard"


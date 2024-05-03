# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
from odoo import _, api, fields, models

from odoo.addons.sale_pdf_quote_builder import utils


class SalePDFQuoteBuilderWhitelistingWizard(models.TransientModel):
    _name = 'sale.pdf.quote.builder.whitelisting.wizard'
    _description = "Sale PDF Quote Builder Whitelisting Wizard"

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res_id = self.env.context.get('active_id')
        res_model = self.env.context.get('active_model')
        if res_id and res_model:
            res.update({'res_model': res_model, 'res_id': res_id})
        return res

    res_model = fields.Char("Related Document Model", required=True)
    res_id = fields.Integer("Related Document ID", required=True)
    restricted_fields = fields.Json()
    sale_pdf_quote_builder_whitelisting_wizard_line_ids = fields.One2many(
        'sale.pdf.quote.builder.whitelisting.wizard.line',
        'sale_pdf_quote_builder_whitelisting_wizard_id',
    )

    @api.onchange('restricted_fields')
    def _get_wizard_lines(self):
        """Use Wizard lines to TODO edm"""
        for wizard in self:
            if wizard.restricted_fields:
                lines_values = []
                print("restricted_fields: ", wizard.restricted_fields)
                restricted_fields = json.loads(wizard.restricted_fields)
                print("test: ", [(model, field) for model, fields in restricted_fields.items() for field in fields])
                for model, fields in restricted_fields.items():
                    lines_values.extend([{'model': model, 'field': field} for field in fields])

                wizard.sale_pdf_quote_builder_whitelisting_wizard_line_ids = [(6, 0, [])] + [(0, 0, vals) for vals in lines_values]  # TODO edm: Command

class SalePdfQuoteBuilderWhitelistingLine(models.TransientModel):
    _name = 'sale.pdf.quote.builder.whitelisting.wizard.line'
    _description = "SalePdfQuoteBuilderWhitelistingLine transient representation"

    sale_pdf_quote_builder_whitelisting_wizard_id = fields.Many2one(
        'sale.pdf.quote.builder.whitelisting.wizard',
        'Sale PDF Quote Builder Whitelisting Wizard',
        required=True,
        ondelete='cascade',
    )
    model = fields.Char()
    field = fields.Char()
    selected = fields.Boolean()

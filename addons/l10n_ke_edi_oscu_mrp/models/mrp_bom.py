# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import UserError

from odoo import api, fields, models, _, Command

import json

class MrpBom(models.Model):
    """ Defines bills of material for a product or a product template """
    _inherit = 'mrp.bom'

    fiscal_country_codes = fields.Char(compute='_compute_fiscal_country_codes')
    l10n_ke_validation_message = fields.Json(compute='_compute_l10n_ke_validation_message')

    @api.depends('company_id')
    @api.depends_context('allowed_company_ids')
    def _compute_fiscal_country_codes(self):
        for record in self:
            allowed_companies = record.company_id or self.env.companies
            record.fiscal_country_codes = ",".join(allowed_companies.mapped('account_fiscal_country_id.code'))

    # TODO - this is horrible, and might also be a performance nightmare. Though there might be no other way to do this considering the exact behaviour we want
    @api.depends(
        'product_id.l10n_ke_packaging_unit_id',
        'product_id.l10n_ke_packaging_quantity',
        'product_id.l10n_ke_origin_country_id',
        'product_id.l10n_ke_tax_type_code',
        'product_id.l10n_ke_product_type_code',
        'product_id.uom_id.l10n_ke_quantity_unit_id.code',
        'product_tmpl_id.product_variant_ids.l10n_ke_packaging_unit_id',
        'product_tmpl_id.product_variant_ids.l10n_ke_packaging_quantity',
        'product_tmpl_id.product_variant_ids.l10n_ke_origin_country_id',
        'product_tmpl_id.product_variant_ids.l10n_ke_tax_type_code',
        'product_tmpl_id.product_variant_ids.l10n_ke_product_type_code',
        'product_tmpl_id.product_variant_ids.uom_id.l10n_ke_quantity_unit_id.code',
        'bom_line_ids.product_id',
        'bom_line_ids.product_id.l10n_ke_packaging_unit_id',
        'bom_line_ids.product_id.l10n_ke_packaging_quantity',
        'bom_line_ids.product_id.l10n_ke_origin_country_id',
        'bom_line_ids.product_id.l10n_ke_tax_type_code',
        'bom_line_ids.product_id.l10n_ke_product_type_code',
        'bom_line_ids.product_id.uom_id.l10n_ke_quantity_unit_id.code',
    )
    def _compute_l10n_ke_validation_message(self):
        for bom in self:
            messages = {}
            products = bom.product_id or bom.product_tmpl_id.product_variant_ids
            products |= bom.bom_line_ids.product_id
            if (validation_message := products._l10n_ke_get_validation_messages(is_invoice=False)):
                messages.update({'product_warning': validation_message})
            bom.l10n_ke_validation_message = messages

    def action_l10n_ke_send_bom(self): # TODO - docstring containing some explanation of the BOM endpoint
        self.ensure_one()
        # Search for all variants for which this BoM is valid
        variants = self.product_id or self.product_tmpl_id.product_variant_ids
        contents = []
        if (blocking := [msg for msg in (self.l10n_ke_validation_message or {}).values() if msg.get('blocking')]):
            raise UserError(_(
                "This bill of materials cannot be registered on eTIMS until following points are resolved:\n%s",
                '\n'.join([f"- {msg['message']}" for msg in blocking]),
            ))

        if (unregistered := (variants | self.bom_line_ids.product_id).filtered(lambda p: not p.l10n_ke_item_code)):
            for product in unregistered:
                product.action_l10n_ke_oscu_save_item()

        for product in variants:
            for bom_line in self.bom_line_ids:
                content = {
                    "itemCd": product.l10n_ke_item_code,
                    "cpstItemCd": bom_line.product_id.l10n_ke_item_code,
                    "cpstQty": bom_line.product_qty,
                    **self.env.company._l10n_ke_get_user_dict(bom_line.create_uid, bom_line.write_uid),
                }
                error, data, _date = bom_line.company_id._l10n_ke_call_etims('saveItemComposition', content)
                if error:
                    raise UserError(error['message'])
                print(content, "response:", data)
                contents.append(content)
        # If no error: message_post
        if contents:
            self.env['ir.attachment'].create({
                'name': 'KRA ' + self.display_name + '.json',
                'res_model': 'mrp.bom',
                'res_id': self.id,
                'raw': "\n".join(json.dumps(p, indent=4) for p in contents),
                })
        self.message_post(body=_("BoM successfully sent to KRA"))

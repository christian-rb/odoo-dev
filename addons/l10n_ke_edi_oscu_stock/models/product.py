# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import _, api, Command, fields, models
from odoo.exceptions import UserError

from odoo.tools.float_utils import json_float_round


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_l10n_ke_oscu_save_stock_master(self):
        if self.product_variant_count != 1:
            raise UserError(_("As you have multiple variants, please do it for them individually. "))
        return self.product_variant_ids.action_l10n_ke_oscu_save_stock_master()

    @api.depends_context('allowed_company_ids')
    def _compute_invoice_policy(self):
        """ Set invoicing policy to on delivery for Kenyan products"""
        kenyan_products = self.env['product.template']
        if 'KE' in self.env.companies.mapped('country_code'):
            kenyan_products = self.filtered(lambda t: t.type == 'product')
            kenyan_products.invoice_policy = 'delivery'
        super(ProductTemplate, self - kenyan_products)._compute_invoice_policy()

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_l10n_ke_oscu_fetch_items(self):
        """ Just there for the automated tests testing the entire api"""
        last_request_date = self.env['ir.config_parameter'].get_param('l10n_ke_edi_oscu.last_fetch_items_request_date', '20180101000000')
        error, data, date = self.env.company._l10n_ke_call_etims('selectItemList', {'lastReqDt': last_request_date})
        raise UserError((error or '') + (data or ''))

    def _l10n_ke_oscu_save_stock_master_content(self, qty_to_add=0.0):
        """ The qty_to_add allows for correcting for moves not being sent yet (because the invoice needs to be generated first e.g."""
        self.ensure_one()
        whs = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)])
        content = {
            'itemCd':      self.l10n_ke_item_code,
            'rsdQty':      json_float_round(self.with_context(warehouse=whs.ids).qty_available + qty_to_add, 2),
            **self.env.company._l10n_ke_get_user_dict(self.create_uid, self.write_uid),
        }
        return content

    def _l10n_ke_save_stock_master(self, qty_to_add=0.0):
        self.ensure_one()
        content = self._l10n_ke_oscu_save_stock_master_content(qty_to_add=qty_to_add)
        error, dummy, dummy = self.env.company._l10n_ke_call_etims('saveStockMaster', content)
        return error, content

    def action_l10n_ke_oscu_save_stock_master(self):
        for product in self:
            error, content = product._l10n_ke_save_stock_master()
            if error:
                raise UserError(error['message'])

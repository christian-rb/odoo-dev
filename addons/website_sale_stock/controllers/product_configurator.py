# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.http import request

from odoo.addons.website_sale.controllers.product_configurator import (
    WebsiteSaleProductConfiguratorController
)


class WebsiteSaleStockProductConfiguratorController(WebsiteSaleProductConfiguratorController):

    def _get_basic_product_information(self, product_or_template, pricelist, combination, **kwargs):
        """ Override to append stock data. """
        basic_product_information = super()._get_basic_product_information(
            product_or_template, pricelist, combination, **kwargs
        )

        if request.is_frontend:
            basic_product_information.update({
                'product_type': product_or_template.type,
                'allow_out_of_stock_order': product_or_template.allow_out_of_stock_order,
                'free_qty': request.website._get_product_available_qty(
                    product_or_template.sudo(), **kwargs
                ) if product_or_template.is_product_variant else 0
            })
        return basic_product_information

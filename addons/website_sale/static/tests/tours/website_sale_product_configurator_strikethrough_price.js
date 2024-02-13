/** @odoo-module **/

import { registry } from '@web/core/registry';
import configuratorTourUtils from "@sale/js/tours/product_configurator_tour_utils";

registry
    .category('web_tour.tours')
    .add('website_sale_product_configurator_strikethrough_price', {
        test: true,
        url: '/shop?search=Main product',
        steps: () => [
            {
                content: "Select Main product",
                trigger: '.oe_product_cart a:contains("Main product")',
            },
            {
                content: "Click on add to cart",
                trigger: '#add_to_cart',
            },
            configuratorTourUtils.assertProductPrice("Main product", '50.00'),
            configuratorTourUtils.assertProductStrikethroughPrice("Main product", '100.00'),
            configuratorTourUtils.assertOptionalProductPrice("Optional product", '5.00'),
            configuratorTourUtils.assertOptionalProductStrikethroughPrice(
                "Optional product", '10.00'
            ),
        ],
   });

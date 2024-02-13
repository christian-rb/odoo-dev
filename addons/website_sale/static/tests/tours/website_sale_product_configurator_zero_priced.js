/** @odoo-module **/

import { registry } from '@web/core/registry';
import configuratorTourUtils from '@sale/js/tours/product_configurator_tour_utils';

registry
    .category('web_tour.tours')
    .add('website_sale_product_configurator_zero_priced', {
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
            // Assert that the "Zero-priced" variant of the optional product can't be sold.
            configuratorTourUtils.assertOptionalProductZeroPriced(
                "Optional product (Zero-priced)"
            ),
            // Add the "Zero-priced" variant by selecting the "One-priced" variant, adding it, and
            // selecting the "Zero-priced" variant again.
            configuratorTourUtils.selectAttribute("Optional product", "Price", "One-priced"),
            configuratorTourUtils.addOptionalProduct("Optional product (One-priced)"),
            configuratorTourUtils.selectAttribute("Optional product", "Price", "Zero-priced"),
            // Assert that the "Zero-priced" variant of the optional product still can't be sold.
            configuratorTourUtils.assertProductZeroPriced("Optional product (Zero-priced)"),
        ],
    });

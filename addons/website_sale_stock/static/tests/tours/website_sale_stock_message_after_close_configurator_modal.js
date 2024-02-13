/** @odoo-module **/

import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add('website_sale_stock_message_after_close_onfigurator_modal_with_optional_products', {
    // This tour relies on a data created from the python test.
    test: true,
    url: '/shop?search=Product With Optional (TEST)',
    steps: () => [{
        content: "Select Customizable Desk",
        trigger: '.oe_product_cart a:contains("Product With Optional (TEST)")',
    }, {
        content: "Check that the stock quantity is displayed and correct",
        trigger: '#threshold_message:contains("30")',
        isCheck: true,
    }, {
        content: "Add to cart",
        trigger: '#add_to_cart',
    }, {
        content: "Continue shoppping",
        extra_trigger: 'table.o_sale_product_configurator_table',
        trigger: 'button:contains(Continue Shopping)',
    }, {
        content: "Check that the stock quantity is displayed and correct after adding to cart",
        trigger: '#threshold_message:contains("29")',
        isCheck: true,
    }
    ]
});

registry.category("web_tour.tours").add('website_sale_stock_message_after_close_onfigurator_modal_without_optional_products', {
    // This tour relies on a data created from the python test.
    test: true,
    url: '/shop?search=Product Without Optional (TEST)',
    steps: () => [{
        content: "Select Office Lamp",
        trigger: '.oe_product_cart a:contains("Product Without Optional (TEST)")',
    }, {
        content: "Check that the stock quantity is displayed and correct",
        trigger: '#threshold_message:contains("30")',
        isCheck: true,
    }, {
        content: "Add to cart",
        trigger: '#add_to_cart',
    }, {
        content: "Check that the stock quantity is displayed and correct after adding to cart",
        trigger: '#threshold_message:contains("29")',
        isCheck: true,
    }
    ]
});

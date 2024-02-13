/** @odoo-module **/

    import { registry } from "@web/core/registry";

    registry.category("web_tour.tours").add("shop_custom_attribute_value", {
        url: "/shop?search=Customizable Desk",
        test: true,
        steps: () => [{
        content: "click on Customizable Desk",
        trigger: '.oe_product_cart a:contains("Customizable Desk (TEST)")',
    }, {
        trigger: 'li.js_attribute_value span:contains(Custom)',
        extra_trigger: 'li.js_attribute_value',
    }, {
        trigger: 'input.variant_custom_value',
        run: "edit Wood",
    }, {
        id: 'add_cart_step',
        trigger: 'a:contains(Add to cart)',
    },
    {
        trigger: 'button:contains(Proceed to Checkout)',
    },
    {
        trigger: 'span:contains(Custom: Wood)',
        extra_trigger: '#cart_products',
        isCheck: true,
    }]});

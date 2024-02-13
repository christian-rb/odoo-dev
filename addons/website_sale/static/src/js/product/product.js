/** @odoo-module **/

import { formatCurrency } from '@web/core/currency';
import { patch } from '@web/core/utils/patch';
import { Product } from '@sale/js/product/product';

patch(Product, {
    props: {
        ...Product.props,
        strikethrough_price: { type: Number, optional: true },
        can_be_sold: { type: Boolean, optional: true },
        category_name: { type: String, optional: true },
        currency_name: { type: String, optional: true },
    },
});

patch(Product.prototype, {
    /**
     * Return the strikethrough price, formatted using the environment's currency.
     *
     * @return {String} - The formatted strikethrough price.
     */
    getFormattedStrikethroughPrice() {
        return formatCurrency(this.props.strikethrough_price, this.env.getCurrencyId());
    }
});

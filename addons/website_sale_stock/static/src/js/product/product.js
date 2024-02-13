/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { Product } from '@sale/js/product/product';

patch(Product, {
    props: {
        ...Product.props,
        product_type: { type: String, optional: true },
        free_qty: { type: Number, optional: true },
        allow_out_of_stock_order: { type: Boolean, optional: true },
    },
});

patch(Product.prototype, {
    /**
     * Return whether this product is out of stock.
     *
     * @return {Boolean} - Whether this product is out of stock.
     */
    isOutOfStock() {
        return !this.env.isQuantityAllowed(this.props.product_tmpl_id, 1);
    }
});

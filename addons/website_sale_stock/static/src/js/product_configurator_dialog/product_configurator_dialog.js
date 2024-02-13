/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { useSubEnv } from '@odoo/owl';
import {
    ProductConfiguratorDialog
} from '@sale/js/product_configurator_dialog/product_configurator_dialog';

patch(ProductConfiguratorDialog.prototype, {
    setup() {
        super.setup(...arguments);

        useSubEnv({
            isQuantityAllowed: this._isQuantityAllowed.bind(this),
        });
    },

    async _setQuantity(productTmplId, quantity) {
        if (!this._isQuantityAllowed(productTmplId, quantity)) {
            const product = this._findProduct(productTmplId);
            quantity = product.free_qty;
        }
        return super._setQuantity(productTmplId, quantity);
    },

    /**
     * Whether the provided product quantity can be added to the cart.
     *
     * @param {Number} productTmplId - The product template id, as a `product.template` id.
     * @param {Number} quantity - The new quantity of the product.
     * @return {Boolean} - Whether the provided product quantity can be added to the cart.
     */
    _isQuantityAllowed(productTmplId, quantity) {
        const product = this._findProduct(productTmplId);
        return product.product_type !== 'product' ||
            product.free_qty >= quantity ||
            product.allow_out_of_stock_order;
    },
});

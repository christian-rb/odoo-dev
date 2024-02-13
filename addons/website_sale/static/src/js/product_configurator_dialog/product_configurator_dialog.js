/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { useSubEnv } from '@odoo/owl';
import {
    ProductConfiguratorDialog
} from '@sale/js/product_configurator_dialog/product_configurator_dialog';

patch(ProductConfiguratorDialog, {
    props: {
        ...ProductConfiguratorDialog.props,
        isFrontend: { type: Boolean, optional: true },
        options: {
            type: Object,
            optional: true,
            shape: {
                isMainProductConfigurable: { type: Boolean, optional: true },
            },
        },
    },
});

patch(ProductConfiguratorDialog.prototype, {
    setup() {
        super.setup(...arguments);

        if (this.props.isFrontend) {
            this.getValuesUrl = '/website_sale_product_configurator/get_values';
            this.createProductUrl = '/website_sale_product_configurator/create_product';
            this.updateCombinationUrl = '/website_sale_product_configurator/update_combination';
            this.getOptionalProductsUrl = '/website_sale_product_configurator/get_optional_products';
        }

        useSubEnv({
            isMainProductConfigurable: this.props.options?.isMainProductConfigurable ?? true,
        });
    },
});

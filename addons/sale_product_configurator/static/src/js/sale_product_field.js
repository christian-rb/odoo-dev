/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { SaleOrderLineProductField } from '@sale/js/sale_product_field';
import { serializeDateTime } from "@web/core/l10n/dates";
import { applyProduct } from "@product/js/product_configurator/product_configurator_field";
import { SaleProductConfiguratorDialog } from "@sale_product_configurator/js/product_configurator_dialog/product_configurator_dialog";

patch(SaleOrderLineProductField.prototype, {
    get productConfiguratorDialogComponent() {
        if (this.props.record.model.config.resModel === 'sale.order') {
            return SaleProductConfiguratorDialog;
        } else {
            super.productConfiguratorDialogComponent;
        }
    },

    get productUomFieldName() {
        if (this.props.record.model.config.resModel === 'sale.order') {
            return 'product_uom';
        } else {
            return super.productUomFieldName;
        }
    },

    get productTemplateFieldName() {
        if (this.props.record.model.config.resModel === 'sale.order') {
            return 'product_template_id';
        } else {
            return super.productTemplateFieldName;
        }
    },

    /**
     * Override of `product` to open the grid configurator if requested.
     *
     * @param {Object} result - values provided by `product_template.get_single_product_variant`
     */
    async _openConfigurator(result) {
        if (result.mode && result.mode === 'matrix') {
            // only triggered when sale_product_matrix is installed.
            this._openGridConfigurator();
        } else {
            super._openConfigurator();
        }
    },

    async getProductConfiguratorDialogProps() {
        const saleOrderRecord = this.props.record.model.root;
        let productConfiguratorDialogProps = await super.getProductConfiguratorDialogProps(
            ...arguments
        );
        Object.assign(productConfiguratorDialogProps, {
            pricelistId: saleOrderRecord.data.pricelist_id[0],
            currencyId: saleOrderRecord.data.currency_id[0],
            soDate: serializeDateTime(saleOrderRecord.data.date_order),
        })
        return productConfiguratorDialogProps;
    },

    async saveProductConfiguratorDialog(mainProduct, optionalProducts) {
        await super.saveProductConfiguratorDialog(...arguments);

        this._onProductUpdate();
        const saleOrderRecord = this.props.record.model.root;
        saleOrderRecord.data.order_line.leaveEditMode();
        for (const optionalProduct of optionalProducts) {
            const line = await saleOrderRecord.data.order_line.addNewRecord({
                position: 'bottom',
                mode: "readonly",
            });
            await applyProduct(line, this.quantityFieldName, optionalProduct);
        }
    },

    async discardProductConfiguratorDialog() {
        super.discardProductConfiguratorDialog(...arguments);
        const saleOrderRecord = this.props.record.model.root;
        saleOrderRecord.data.order_line.delete(this.props.record);
    },
});

/** @odoo-module **/

import { registry } from "@web/core/registry";
import { productField, ProductField } from "@product/js/product_configurator/product_configurator_field";

export class SaleOrderLineProductField extends ProductField {

    get isProductClickable() {
        // product form should be accessible if the widget field is readonly
        // or if the line cannot be edited (e.g. locked SO)
        return super.isProductClickable || (
            this.props.record.model.root.activeFields.order_line &&
            this.props.record.model.root._isReadonly("order_line")
        );
    }

    get hasConfigurationButton() {
        return this.isConfigurableLine || super.hasConfigurationButton;
    }

    get isConfigurableLine() {
        return false;
    }

    onClick(ev) {
        // Override to get internal link to products in SOL that cannot be edited
        if (this.props.readonly) {
            ev.stopPropagation();
            this.openAction();
        } else {
            super.onClick(ev);
        }
    }

    async _onProductUpdate() {} // event_booth_sale, event_sale, sale_renting

    onEditConfiguration() {
        if (this.isConfigurableLine) {
            this._editLineConfiguration();
        } else {
            super._editProductConfiguration();
        }
    }

    _editLineConfiguration() {} // event_booth_sale, event_sale, sale_renting
}

export const saleOrderLineProductField = {
    ...productField,
    component: SaleOrderLineProductField,
};

registry.category("fields").add("sol_product_many2one", saleOrderLineProductField);

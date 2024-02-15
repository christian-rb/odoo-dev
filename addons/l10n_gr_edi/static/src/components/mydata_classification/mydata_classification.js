/** @odoo-module **/

import { registry } from "@web/core/registry";

import { SelectionField, selectionField } from "@web/views/fields/selection/selection_field";

export class DynamicSelectionField extends SelectionField {

    /** To be overridden **/
    get availableOptions() {
        return [];
    }

    /** Override **/
    get options() {
        const availableOptions = this.availableOptions;
        return super.options.filter(x => availableOptions.includes(x[0]));
    }

}

export class GreeceInvoiceType extends DynamicSelectionField {
    /** Override **/
    get availableOptions() {
        return this.props.record.data.l10n_gr_edi_available_inv_type.split(",");
    }
}

export class GreeceClassificationCategory extends DynamicSelectionField {
    /** Override **/
    get availableOptions() {
        return this.props.record.data.l10n_gr_edi_available_cls_category.split(",");
    }
}

export class GreeceClassificationType extends DynamicSelectionField {
    /** Override **/
    get availableOptions() {
        return this.props.record.data.l10n_gr_edi_available_cls_type.split(",");
    }
}

export class GreeceClassificationVat extends DynamicSelectionField {
    /** Override **/
    get availableOptions() {
        return this.props.record.data.l10n_gr_edi_available_cls_vat.split(",");
    }
}

registry.category("fields").add("selection_l10n_gr_edi_inv_type", {
    ...selectionField,
    component: GreeceInvoiceType,
});
registry.category("fields").add("selection_l10n_gr_edi_cls_category", {
    ...selectionField,
    component: GreeceClassificationCategory,
});
registry.category("fields").add("selection_l10n_gr_edi_cls_type", {
    ...selectionField,
    component: GreeceClassificationType,
});
registry.category("fields").add("selection_l10n_gr_edi_cls_vat", {
    ...selectionField,
    component: GreeceClassificationVat,
});

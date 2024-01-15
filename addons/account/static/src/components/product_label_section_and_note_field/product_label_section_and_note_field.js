import { _t } from "@web/core/l10n/translation";
import { AutoComplete } from "@web/core/autocomplete/autocomplete";
import { Many2XAutocomplete } from "@web/views/fields/relational_utils";
import { Many2OneField, many2OneField } from "@web/views/fields/many2one/many2one_field";
import { registry } from "@web/core/registry";
import {
    SectionAndNoteListRenderer,
    sectionAndNoteFieldOne2Many,
} from "@account/components/section_and_note_fields_backend/section_and_note_fields_backend";
import { useProductAndLabelAutoresize } from "@account/core/utils/product_and_label_autoresize";
import { onPatched, useEffect, useRef, useState } from "@odoo/owl";
import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";

export class ProductLabelSectionAndNoteListRender extends SectionAndNoteListRenderer {
    getCellTitle(column, record) {
        // When using this list renderer, we don't want the product_id cell to have a tooltip with its label.
        if (column.name === "product_id") {
            return;
        }
        super.getCellTitle(column, record);
    }

    getActiveColumns(list) {
        let activeColumns = super.getActiveColumns(list);

        if (activeColumns.find((col) => col.name === "product_id") && activeColumns.find((col) => col.name === "name")) {
            activeColumns = activeColumns.filter((col) => col.name !== "name");
            list.records.forEach(record => {
                record.columnIsProductAndLabel = true;
            });
        }
        else if (activeColumns.find((col) => col.name === "product_id") && !activeColumns.find((col) => col.name === "name")) {
            list.records.forEach(record => {
                record.columnIsProductAndLabel = false;
            });
        }

        // This section is used to determine if the "Product" column is used to make a section or a note
        // This has to be done after the previous if statement because we need to know if the "name" column is shown
        if (activeColumns.some((col) => col.name === "product_id")) {
            this.titleField = "product_id";
            activeColumns = activeColumns.filter((col) => col.name !== "name");
        } else {
            this.titleField = "name";
        }

        return activeColumns;
    }
}

export class ProductLabelSectionAndNoteOne2Many extends X2ManyField {
    static components = {
        ...X2ManyField.components,
        ListRenderer: ProductLabelSectionAndNoteListRender,
    };
}

export const productLabelSectionAndNoteOne2Many = {
    ...x2ManyField,
    component: ProductLabelSectionAndNoteOne2Many,
    additionalClasses: sectionAndNoteFieldOne2Many.additionalClasses,
};

registry
    .category("fields")
    .add("product_label_section_and_note_field_o2m", productLabelSectionAndNoteOne2Many);

export class ProductLabelSectionAndNoteAutocomplete extends AutoComplete {

    onInputKeydown(event) {
        if (event.key === 'Enter') {
            super.onInputKeydown(event);
            const labelVisibilityButton = document.getElementById('labelVisibilityButton');
            const labelTextarea = document.getElementById('labelTextarea');
            if (labelVisibilityButton && !labelTextarea) {
                labelVisibilityButton.click();
            } else {
                labelTextarea.focus();
            }
            event.stopPropagation();
            event.preventDefault();
        } else {
            super.onInputKeydown(event);
        }
    }
}

export class ProductLabelSectionAndNoteFieldAutocomplete extends Many2XAutocomplete {
    static components = {
        ...Many2XAutocomplete.components,
        AutoComplete: ProductLabelSectionAndNoteAutocomplete,
    };
    static props = {
        ...Many2XAutocomplete.props,
        isNote: { type: Boolean },
        isSection: { type: Boolean },
        onFocusout: { type: Function, optional: true },
        updateLabel: { type: Function, optional: true },
    };
    static template = "account.ProductLabelSectionAndNoteFieldAutocomplete";
    setup() {
        super.setup();
        this.input = useRef("section_and_note_input");
    }

    get isSectionOrNote() {
        return this.props.isSection || this.props.isNote;
    }

    get isSection() {
        return this.props.isSection;
    }
}

export class ProductLabelSectionAndNoteField extends Many2OneField {
    static components = {
        ...Many2OneField.components,
        Many2XAutocomplete: ProductLabelSectionAndNoteFieldAutocomplete,
    };
    static template = "account.ProductLabelSectionAndNoteField";

    setup() {
        super.setup();
        this.labelVisibility = useState({value: false});
        this.switchToLabel = false;
        this.columnIsProductAndLabel = useState({value: this.props.record.columnIsProductAndLabel});
        this.labelAutoresizeRef = useRef("labelAutoresizeRef");
        useProductAndLabelAutoresize(this.labelAutoresizeRef, {targetParentName: "product_id"});
        this.productAutoresizeRef = useRef("productAutoresizeRef");
        useProductAndLabelAutoresize(this.productAutoresizeRef, {targetParentName: "product_id"});

        useEffect(
            () => {
                this.columnIsProductAndLabel.value = this.props.record.columnIsProductAndLabel;
            },
            () => [this.props.record.columnIsProductAndLabel]
        );

        onPatched(() => {
            const textarea = document.getElementById('labelTextarea');
            if (textarea && this.switchToLabel) {
                this.switchToLabel = false;
                textarea.focus();
            }
        });
    }

    get productName() {
        return this.props.record.data.product_id[1];
    }

    get label() {
        return this.props.record.data.name;
    }

    get Many2XAutocompleteProps() {
        const props = super.Many2XAutocompleteProps;
        props.isSection = this.isSection(this.props.record);
        props.isNote = this.isNote(this.props.record);
        props.placeholder = _t("Search a product");
        props.updateLabel = this.updateLabel.bind(this);
        return props;
    }

    get isProductClickable() {
        return this.props.record.model.root.data.state != "draft";
    }

    get isSectionOrNote() {
        return this.isSection(this.props.record) || this.isNote(this.props.record);
    }

    get sectionAndNoteClasses() {
        if (this.isSection()) {
            return "fw-bold";
        } else if (this.isNote()) {
            return "fst-italic";
        }
        return "";
    }

    isSection(record = null) {
        record = record || this.props.record;
        return record.data.display_type === "line_section";
    }

    isNote(record = null) {
        record = record || this.props.record;
        return record.data.display_type === "line_note";
    }

    switchLabelVisibility() {
        this.labelVisibility.value = !this.labelVisibility.value;
        this.switchToLabel = true;
    }

    updateLabel(value) {
        this.props.record.update({ name: value });
    }
}

export const productLabelSectionAndNoteField = {
    ...many2OneField,
    component: ProductLabelSectionAndNoteField,
    ListRenderer: ProductLabelSectionAndNoteListRender,
};
registry
    .category("fields")
    .add("product_label_section_and_note_field", productLabelSectionAndNoteField);

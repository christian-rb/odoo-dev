/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { Many2OneField } from "@web/views/fields/many2one/many2one_field";
import { ReferenceField, referenceField } from "@web/views/fields/reference/reference_field";

export class EventMailTemplateReferenceField extends ReferenceField {
    static template = "event.mail_template_reference_field";
    static components = {
        Many2OneField,
    };
    get m2oProps() {
        const props = super.m2oProps;
        // makes editing in the list view much easier
        return { ...props, canOpen: false };
    }
}

export const eventMailTemplateReferenceField = {
    ...referenceField,
    component: EventMailTemplateReferenceField,
    displayName: _t("Event Mail Template Reference"),
};

registry.category("fields").add("event_mail_template_reference_field", eventMailTemplateReferenceField);

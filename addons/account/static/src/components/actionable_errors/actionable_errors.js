/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component } from "@odoo/owl";

export class ActionableErrors extends Component {
    static template = "account.ActionableErrors";
    static props = { errorData: {type: Object} };

    setup() {
        super.setup();
        this.actionService = useService("action");
    }

    async handleOnClick(clickedError) {
        this.actionService.doAction(clickedError.action);
    }

    get errorData() {
        return this.props.errorData;
    }

    get sortedActionableErrors() {
        // With no fixed errorData set, then information is stored
        // on a jsonb field in the DB. jsonb fields lose order
        // so we sort it back by ("critical", key)
        return Object.fromEntries(Object.entries(this.errorData).sort((a, b) =>
              a[1]["critical"] && !b[1]["critical"] ? -1
            : !a[1]["critical"] && b[1]["critical"] ? 1
            : a[0].localeCompare(b[0])
        ));
    }
}

export class ActionableErrorsField extends ActionableErrors {
    static props = { ...standardFieldProps };

    get errorData() {
        return this.props.record.data[this.props.name];
    }
}

export const actionableErrorsField = {component: ActionableErrorsField};
registry.category("fields").add("actionable_errors", actionableErrorsField);

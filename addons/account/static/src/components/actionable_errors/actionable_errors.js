/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

const DISPLAY_ORDER = [
    'danger',
    'warning',
    'info',
];

export class ActionableErrors extends Component {
    static props = { ...standardFieldProps };
    static template = "account.ActionableErrors";

    async handleOnClick(errorData){
        this.env.model.action.doAction(errorData.action);
    }

    get sortedActionableErrors() {
        let data = this.props.record.data[this.props.name];
        return Object.fromEntries(Object.entries(data).sort((a, b) => (
            DISPLAY_ORDER.indexOf(a[1]["level"] || "warning") - DISPLAY_ORDER.indexOf(b[1]["level"] || "warning"))
        ));
    }
}

export const actionableErrors = {component: ActionableErrors};
registry.category("fields").add("actionable_errors", actionableErrors);

/** @odoo-module */

import { registry } from '@web/core/registry';
import {
    StateSelectionField,
    stateSelectionField,
} from "@web/views/fields/state_selection/state_selection_field";

export class ContractStateSelection extends StateSelectionField {
    setup() {
        super.setup();
        this.colorPrefix = 'o_status_bubble o_color_bubble_';
        this.colors = {
            'blocked': 30,
            'waiting': 31,
            'done': 32,
        };
    }
}

export const contractStateSelection = {
    ...stateSelectionField,
    component: ContractStateSelection,
};

registry.category("fields").add("contract_state_selection", contractStateSelection);

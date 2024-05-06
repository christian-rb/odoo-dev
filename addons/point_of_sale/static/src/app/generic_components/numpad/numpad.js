/** @odoo-module */

import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";

export const buttonsType = {
    type: Array,
    element: [
        {
            type: Object,
            shape: {
                value: String,
                text: { type: String, optional: true },
                class: { type: String, optional: true },
                disabled: { type: Boolean, optional: true },
            },
        },
        Number,
        String,
    ],
};

export function getDefaultLastRow(env) {
    const decimalButton = { value: env.services.localization.decimalPoint };
    return [{ value: "-", text: "+/-" }, { value: "0" }, decimalButton];
}

export const BACKSPACE = { value: "Backspace", text: "⌫" };

export function getButtons(lastRow, rightColumn) {
    return [
        { value: "1" },
        { value: "2" },
        { value: "3" },
        ...(rightColumn ? [rightColumn[0]] : []),
        { value: "4" },
        { value: "5" },
        { value: "6" },
        ...(rightColumn ? [rightColumn[1]] : []),
        { value: "7" },
        { value: "8" },
        { value: "9" },
        ...(rightColumn ? [rightColumn[2]] : []),
        ...lastRow,
        ...(rightColumn ? [rightColumn[3]] : []),
    ];
}

export function enhancedButtons(env) {
    return getButtons(getDefaultLastRow(env), [
        { value: "+10" },
        { value: "+20" },
        { value: "+50" },
        BACKSPACE,
    ]);
}

export class Numpad extends Component {
    static template = "point_of_sale.Numpad";
    static props = {
        class: { type: String, optional: true },
        onClick: { type: Function, optional: true },
        buttons: { type: buttonsType, optional: true },
    };
    static defaultProps = {
        class: "",
    };
    get buttons() {
        return this.props.buttons || getButtons(getDefaultLastRow(this.env));
    }
    setup() {
        if (!this.props.onClick) {
            this.numberBuffer = useService("number_buffer");
            this.onClick = (buttonValue) => this.numberBuffer.sendKey(buttonValue);
        } else {
            this.onClick = this.props.onClick;
        }
    }
}

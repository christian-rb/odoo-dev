import { Component, onMounted, useRef, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class ManageGiftCardPopup extends Component {
    static template = "pos_loyalty.ManageGiftCardPopup";
    static components = { Dialog };
    static props = {
        title: String,
        buttons: { type: Array, optional: true },
        startingValue: { type: String, optional: true },
        placeholder: { type: String, optional: true },
        rows: { type: Number, optional: true },
        getPayload: Function,
        close: Function,
    };
    static defaultProps = {
        startingValue: "",
        placeholder: "",
        rows: 1,
        buttons: [],
    };

    setup() {
        this.state = useState({
            inputValue: this.props.startingValue,
            amountValue: "",
            error: "",
            amountError: "",
        });
        this.inputRef = useRef("input");
        this.amountInputRef = useRef("amountInput");
        onMounted(this.onMounted);
    }

    onMounted() {
        this.inputRef.el.focus();
    }

    confirm() {
        if (!this.validateCode()) {
            return;
        }
        this.props.getPayload(this.state.inputValue, parseFloat(this.state.amountValue));
        this.props.close();
    }

    close() {
        this.props.close();
    }

    buttonClick(button) {
        const lines = this.state.inputValue.split("\n").filter((line) => line !== "");
        if (lines.includes(button.label)) {
            this.state.inputValue = lines.filter((line) => line !== button.label).join("\n");
            button.isSelected = false;
        } else {
            this.state.inputValue = lines.concat(button.label).join("\n");
            button.isSelected = true;
        }
    }

    validateCode() {
        const { inputValue, amountValue } = this.state;
        if (inputValue.trim() === "") {
            this.state.error = "Please enter a gift card code";
            return false;
        }
        if (amountValue.trim() === "") {
            this.state.amountError = "Please enter an amount";
            return false;
        }
        if (isNaN(parseFloat(amountValue))) {
            this.state.amountError = "Amount must be a valid number";
            return false;
        }
        this.state.error = "";
        this.state.amountError = "";
        return true;
    }
}

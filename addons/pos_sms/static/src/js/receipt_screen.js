/** @odoo-module */

import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { useTrackedAsync } from "@point_of_sale/app/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

patch(ReceiptScreen.prototype, {
    setup() {
        super.setup(...arguments);
        const partner = this.currentOrder.get_partner();
        this.state.inputValue = partner?.email || partner?.mobile || partner?.phone;
        this.doSendSms = useTrackedAsync(() => this._sendSmsReceiptToCustomer());
    },

    get is_valid_mobile() {
        const value = this.state.inputValue;
        if (value) {
            const isValidFormat = /^[\d()+-\s]*$/.test(value);
            const phoneNumberLength = value.replace(/[^\d]/g, "").length;
            return isValidFormat && phoneNumberLength > 8 && phoneNumberLength < 15;
        }
        return false;
    },

    get MessageStatus() {
        if (this.state.messageMode === "sms") {
            switch (this.doSendSms.status) {
                case "loading":
                    return {
                        class: "text-info",
                        message: _t("Sending in progress."),
                        status: this.doSendSms.status,
                    };
                case "success":
                    return {
                        class: "successful text-success",
                        message: _t("SMS sent."),
                        status: this.doSendSms.status,
                    };
                case "error":
                    return {
                        class: "failed text-danger",
                        message: _t("Sending SMS failed. Please try again."),
                        status: this.doSendSms.status,
                    };
                default:
                    throw new Error("Shouldn't be reached.");
            }
        }
        return super.MessageStatus;
    },
    async _sendSmsReceiptToCustomer() {
        this.state.messageMode = "sms";
        const phoneNumber = this.state.inputValue;
        await this.pos.data.call("pos.order", "action_sent_message_on_sms", [
            [this.currentOrder.id],
            phoneNumber,
        ]);
    },
});

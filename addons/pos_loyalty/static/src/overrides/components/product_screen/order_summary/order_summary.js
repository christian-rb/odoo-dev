/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { OrderSummary } from "@point_of_sale/app/screens/product_screen/order_summary/order_summary";
import { patch } from "@web/core/utils/patch";
import { ask } from "@point_of_sale/app/store/make_awaitable_dialog";
import { useService } from "@web/core/utils/hooks";
import { ManageGiftCardPopup } from "@pos_loyalty/utils/manage_giftcard_popup/manage_giftcard_popup";
import { loyaltyIdsGenerator } from "@pos_loyalty/overrides/models/pos_store";

patch(OrderSummary.prototype, {
    setup() {
        super.setup(...arguments);
        this.notification = useService("notification");
    },
    async updateSelectedOrderline({ buffer, key }) {
        const selectedLine = this.currentOrder.get_selected_orderline();
        if (key === "-") {
            if (selectedLine && selectedLine.e_wallet_program_id) {
                // Do not allow negative quantity or price in a gift card or ewallet orderline.
                // Refunding gift card or ewallet is not supported.
                this.notification.add(
                    _t("You cannot set negative quantity or price to gift card or ewallet."),
                    4000
                );
                return;
            }
        }
        if (
            selectedLine &&
            selectedLine.is_reward_line &&
            !selectedLine.manual_reward &&
            (key === "Backspace" || key === "Delete")
        ) {
            const reward = selectedLine.reward_id;
            const confirmed = await ask(this.dialog, {
                title: _t("Deactivating reward"),
                body: _t(
                    "Are you sure you want to remove %s from this order?\n You will still be able to claim it through the reward button.",
                    reward.description
                ),
                cancelLabel: _t("No"),
                confirmLabel: _t("Yes"),
            });
            if (confirmed) {
                buffer = null;
            } else {
                // Cancel backspace
                return;
            }
        }
        return super.updateSelectedOrderline({ buffer, key });
    },
    /**
     * 1/ Perform the usual set value operation (super._setValue(val)) if the line being modified
     * is not a reward line or if it is a reward line, the `val` being set is '' or 'remove' only.
     *
     * 2/ Update activated programs and coupons when removing a reward line.
     *
     * 3/ Trigger 'update-rewards' if the line being modified is a regular line or
     * if removing a reward line.
     *
     * @override
     */
    _setValue(val) {
        const selectedLine = this.currentOrder.get_selected_orderline();
        if (!selectedLine) {
            return;
        }
        if (selectedLine.is_reward_line && val === "remove") {
            this.currentOrder.uiState.disabledRewards.add(selectedLine.reward_id.id);
            const coupon = selectedLine.coupon_id;
            if (
                coupon &&
                coupon.id > 0 &&
                this.currentOrder.code_activated_coupon_ids.find((c) => c.code === coupon.code)
            ) {
                coupon.delete();
            }
        }
        if (
            !selectedLine ||
            !selectedLine.is_reward_line ||
            (selectedLine.is_reward_line && ["", "remove"].includes(val))
        ) {
            super._setValue(val);
        }
        if (!selectedLine.is_reward_line || (selectedLine.is_reward_line && val === "remove")) {
            this.pos.updateRewards();
        }
    },

    async _showDecreaseQuantityPopup() {
        const result = await super._showDecreaseQuantityPopup();
        if (result) {
            this.pos.updateRewards();
        }
    },

    getGiftCardCodes() {
        const giftCardCodes = [];
        for (const couponId in this.currentOrder.uiState.couponPointChanges) {
            const couponChange = this.currentOrder.uiState.couponPointChanges[couponId];
            if (couponChange.manual) {
                const code = couponChange.existing_code || couponChange.code;
                giftCardCodes.push(code);
            }
        }
        return giftCardCodes;
    },

    manageGiftCard() {
        this.dialog.add(ManageGiftCardPopup, {
            title: _t("Sell physical gift card OR Manage"),
            placeholder: _t("Enter Gift Card Number"),
            getPayload: async (code, points) => {
                points = parseFloat(points);
                if (isNaN(points)) {
                    console.error("Invalid amount value:", points);
                    return;
                }
                code = code.trim();
                const res = await this.pos.data.searchRead(
                    "loyalty.card",
                    ["&", ["program_type", "=", "gift_card"], ["code", "=", code]],
                    [],
                    { limit: 1 }
                );
                (res && res.length > 0
                    ? this.handleExistingGiftCard
                    : this.handleValidGiftCard
                ).call(this, res[0] || code, points);
            },
        });
    },

    async handleValidGiftCard(code, points) {
        const partner_id = this.currentOrder.get_partner()?.id || false;
        const couponId =
            this.currentOrder.uiState.pendingGiftCardCoupons?.shift() || loyaltyIdsGenerator();
        const program = this.pos.models["loyalty.program"].find(
            (p) => p.program_type === "gift_card"
        );

        this.currentOrder.uiState.couponPointChanges[couponId] = {
            program_id: program?.id,
            coupon_id: couponId,
            points: points,
            code: code,
            partner_id: partner_id,
            manual: true,
        };
    },

    handleExistingGiftCard(giftCardInfo, points) {
        if (this.currentOrder.uiState.pendingGiftCardCoupons?.length) {
            const couponId = this.currentOrder.uiState.pendingGiftCardCoupons.shift();
            delete this.currentOrder.uiState.couponPointChanges[couponId];
        }
        this.currentOrder.uiState.couponPointChanges[giftCardInfo.id] = {
            program_id: giftCardInfo.program_id.id,
            coupon_id: giftCardInfo.id,
            points: points,
            existing_code: giftCardInfo.code,
            manual: true,
        };
    },
});

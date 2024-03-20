/** @odoo-module **/

import { reactive } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";

export const websiteSaleService = {
    dependencies: ['cartNotificationService'],

    async start(env, { cartNotificationService }) {
        let context = reactive({
            nbItemsInCart: sessionStorage.getItem("website_sale_cart_quantity")
        });

        function addToCart(data) {
            _showCartNotification(data.notification_info);
        }

        // TODO VCR add tracking
        // TODO VCR handle navbar from here

        function _showCartNotification(props, options = {}) {
            // Show the notification about the cart
            if (props.lines) {
                cartNotificationService.add(_t("Item(s) added to your cart"), {
                    lines: props.lines,
                    currency_id: props.currency_id,
                    ...options,
                });
            }
            if (props.warning) {
                cartNotificationService.add(_t("Warning"), {
                    warning: props.warning,
                    ...options,
                });
            }
        }


        return { context, addToCart };
    },
}

registry.category("services").add("website_sale", websiteSaleService);

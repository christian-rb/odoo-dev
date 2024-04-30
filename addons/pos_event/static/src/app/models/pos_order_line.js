/** @odoo-module */

import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { patch } from "@web/core/utils/patch";

patch(PosOrderline.prototype, {
    can_be_merged_with(orderline) {
        return (
            this.event_ticket_id?.id === orderline.event_ticket_id?.id &&
            super.can_be_merged_with(...arguments)
        );
    },
});

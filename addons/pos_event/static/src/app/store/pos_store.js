/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
    async setup() {
        await super.setup(...arguments);
        this.onNotified("UPDATE_AVAILABLE_SEATS", (data) => {
            for (const ev of data) {
                if (!ev.event_id) {
                    return;
                }

                const event = this.models["event.event"].get(ev.event_id);
                if (event) {
                    event.seats_available = ev.seats_available;
                }

                if (ev.event_ticket_ids.length) {
                    for (const ticket of ev.event_ticket_ids) {
                        const eventTicket = this.models["event.event.ticket"].get(ticket.ticket_id);
                        if (eventTicket) {
                            eventTicket.seats_available = ticket.seats_available;
                        }
                    }
                }
            }
        });
    },
});

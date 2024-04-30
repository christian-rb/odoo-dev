/** @odoo-module */

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { patch } from "@web/core/utils/patch";
import { EventConfiguratorPopup } from "@pos_event/app/popup/event_configurator_popup/event_configurator_popup";
import { _t } from "@web/core/l10n/translation";

patch(ProductScreen.prototype, {
    get products() {
        const products = super.products;
        const fakeEventProducts = this.pos.models["event.event"]
            .filter(
                (event) =>
                    event.event_ticket_ids.length > 0 &&
                    event.event_ticket_ids.every(
                        (ticket) => ticket.product_id && ticket.product_id.detailed_type === "event"
                    )
            )
            .map((event) => {
                const ticket = event.event_ticket_ids.sort(
                    (a, b) => a.product_id.get_price() - b.product_id.get_price()
                )[0];

                return {
                    ...ticket.product_id,
                    id: `${ticket.product_id.id}-${ticket.id}`,
                    _event_id: ticket.event_id,
                };
            });
        return [...products, ...fakeEventProducts];
    },
    getProductListToNotDisplay() {
        const products = super.getProductListToNotDisplay();
        const eventProducts = this.pos.models["event.event.ticket"].map(
            (ticket) => ticket.product_id?.id
        );
        return [...products, ...eventProducts];
    },
    getProductName(product) {
        if (!product._event_id) {
            return super.getProductName(product);
        }

        return product._event_id.name;
    },
    getProductPrice(product) {
        if (!product._event_id) {
            return super.getProductPrice(product);
        }

        const event = product._event_id;
        const minPrice = Math.min(
            ...event.event_ticket_ids.map((ticket) => ticket.product_id.lst_price)
        );
        return _t("From %s", this.env.utils.formatCurrency(minPrice));
    },
    getProductImage(product) {
        if (!product._event_id) {
            return super.getProductImage(product);
        }

        return `/web/image?model=event.event&id=${product._event_id.id}&field=image&unique=${product._event_id.write_date}`;
    },
    async addProductToOrder(product) {
        if (!product._event_id) {
            return await super.addProductToOrder(product);
        }

        if (product._event_id.seats_available === 0 && product._event_id.seats_limited) {
            this.notification.add("No more seats available for this event", {
                type: "danger",
            });
            return;
        }

        const event = product._event_id;
        const tickets = event.event_ticket_ids.filter(
            (ticket) => ticket.product_id && ticket.product_id.detailed_type === "event"
        );

        const result = await makeAwaitable(this.dialog, EventConfiguratorPopup, {
            tickets: tickets,
        });

        if (!result) {
            this.notification.add("No ticket selected", {
                type: "warning",
            });
            return;
        }

        const ticketId = event.event_ticket_ids.find(
            (ticket) => ticket.product_id.id === result.product.id
        );

        await this.pos.addLineToCurrentOrder({
            product_id: result.product,
            qty: result.qty,
            event_ticket_id: ticketId,
        });
    },
});

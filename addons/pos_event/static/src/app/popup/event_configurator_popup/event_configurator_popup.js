import { Dialog } from "@web/core/dialog/dialog";
import { Component, useState } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ProductCard } from "@point_of_sale/app/generic_components/product_card/product_card";
import { NumericInput } from "@point_of_sale/app/generic_components/inputs/numeric_input/numeric_input";

export class EventConfiguratorPopup extends Component {
    static template = "pos_event.EventConfiguratorPopup";
    static props = ["tickets", "getPayload", "close"];
    static components = {
        Dialog,
        ProductCard,
        NumericInput,
    };
    setup() {
        this.pos = usePos();
        this.state = useState({
            qty: 1,
        });
    }
    getProductProxy(productId) {
        return this.pos.models["product.product"].get(productId);
    }
    selectProduct(product) {
        this.props.getPayload({ product, qty: this.state.qty });
        this.props.close();
    }
    cancel() {
        this.props.close();
    }
    confirm() {
        this.props.getPayload([]);
        this.props.close();
    }
    get tickets() {
        return this.props.tickets.sort((a, b) => b.seats_available - a.seats_available);
    }
}

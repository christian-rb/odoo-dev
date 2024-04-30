/** @odoo-module */
import { MockPosData } from "@point_of_sale/../tests/unit/pos_app_tests";
import { patch } from "@web/core/utils/patch";

patch(MockPosData.prototype, {
    get data() {
        const data = super.data;
        data.models["event.event"] = { relations: {}, fields: {}, data: [] };
        data.models["event.event.ticket"] = { relations: {}, fields: {}, data: [] };
        data.models["event.registration"] = { relations: {}, fields: {}, data: [] };
        return data;
    },
});

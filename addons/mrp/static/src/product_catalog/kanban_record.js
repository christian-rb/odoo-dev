/** @odoo-module */
import { ProductCatalogKanbanRecord } from "@product/product_catalog/kanban_record";
import { ProductCatalogMrpMoveRawLine } from "./mrp_move_raw/mrp_move_raw";
import { patch } from "@web/core/utils/patch";

patch(ProductCatalogKanbanRecord.prototype, {
    setup() {
        super.setup();
    },

    get orderLineComponent() {
        if (this.env.orderResModel === "mrp.production") {
            return ProductCatalogMrpMoveRawLine;
        }
        return super.orderLineComponent;
    },
});

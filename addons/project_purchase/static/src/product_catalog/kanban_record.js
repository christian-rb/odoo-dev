/** @odoo-module **/
import { patch } from "@web/core/utils/patch";

import { ProductCatalogKanbanRecord } from "@product/product_catalog/kanban_record";

patch(ProductCatalogKanbanRecord.prototype, {
    _updateQuantityAndGetPrice() {
        return this.rpc("/product/catalog/update_order_line_info", {
            order_id: this.env.orderId,
            product_id: this.env.productId,
            quantity: this.productCatalogData.quantity,
            res_model: this.env.orderResModel,
            project_id: this.props.record.context.project_id,
        });
    },
});

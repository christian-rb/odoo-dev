import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class Breadcrumb extends Component {
    static template = "web.Breadcrumbs";
    static components = {};
    static props = {
        breadcrumbs: Array,
    };

    setup() {
        this.actionService = useService("action");
    }

    /**
     * Called when an element of the breadcrumbs is clicked.
     *
     * @param {string} jsId
     */
    onBreadcrumbClicked(jsId) {
        this.actionService.restore(jsId);
    }
}

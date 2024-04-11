/** @odoo-module **/

import { registry } from "@web/core/registry";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { Component, useState, onWillStart } from "@odoo/owl";
import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { useService } from "@web/core/utils/hooks";

export class PosActionHelper extends Component {
    static template = "point_of_sale.PosActionHelper";
    static props = ["noContentHelp", "hasChartTemplate"];

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            loadingDemo: false,
            haveAvailableProducts: false,
        });
        onWillStart(async () => {
            this.state.haveAvailableProducts = await this.checkAvailableProducts();
        });
    }

    get shopScenarios() {
        return [
            {
                name: "Clothes",
                description: "Demo sample for a clothes store",
                function_name: "load_onboarding_clothes_scenario",
                icon_file: "clothes-icon.png",
            },
            {
                name: "Furnitures",
                description: "Demo sample to run an office furniture store",
                function_name: "load_onboarding_furniture_scenario",
                icon_file: "furniture-icon.png",
            },
            {
                name: "Bakery",
                description: "Demo sample to sell pastries and bread",
                function_name: "load_onboarding_bakery_scenario",
                icon_file: "bakery-icon.png",
            },
        ];
    }

    get predefinedConfigs() {
        return [
            {
                name: "Retail",
                description: "A simple shop, on a tablet or laptop",
                function_name: "load_onboarding_pos_config_retail",
                icon_file: "/point_of_sale/static/src/img/retail-icon.png",
            },
        ];
    }

    async checkAvailableProducts() {
        await this.orm.call("pos.config", "check_available_products");
    }

    async loadScenarioData(functionName) {
        this.state.loadingDemo = true;
        try {
            await this.orm.call("pos.config", functionName);
        } finally {
            this.env.searchModel.dispatchEvent(new CustomEvent("update"));
        }
    }

    async loadPosConfig(functionName) {
        this.state.loadingDemo = true;
        try {
            await this.orm.call("pos.config", functionName);
        } finally {
            this.env.searchModel.dispatchEvent(new CustomEvent("update"));
        }
    }

    createNewProducts() {
        window.open("/web#action=point_of_sale.action_client_product_menu", "_self");
    }
}

export class PosKanbanRenderer extends KanbanRenderer {
    static template = "point_of_sale.PosKanbanRenderer";
    static components = {
        ...PosKanbanRenderer.components,
        PosActionHelper,
    };

    setup() {
        super.setup();
        onWillStart(async () => {
            const { has_pos_config, has_chart_template } = await this.checkCompanyHasPosConfig();
            this.hasPosConfig = has_pos_config;
            this.hasChartTemplate = has_chart_template;
        });
    }

    async checkCompanyHasPosConfig() {
        return await this.env.services.orm.call("pos.config", "check_company_has_pos_config");
    }
}

export const PosKanbanView = {
    ...kanbanView,
    Renderer: PosKanbanRenderer,
};

registry.category("views").add("pos_dashboard_kanban_view", PosKanbanView);

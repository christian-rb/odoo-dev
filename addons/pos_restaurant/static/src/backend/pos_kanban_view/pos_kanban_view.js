import { PosActionHelper } from "@point_of_sale/backend/pos_kanban_view/pos_kanban_view";
import { patch } from "@web/core/utils/patch";

patch(PosActionHelper.prototype, {
    get restaurantScenarios() {
        return [
            {
                name: "Restaurant",
                description: "Demo sample to run a restaurant",
                function_name: "load_onboarding_restaurant_scenario",
                icon_file: "restaurant-icon.png",
            },
            {
                name: "Bar",
                description: "Demo sample to run a cocktail bar",
                function_name: "load_onboarding_bar_scenario",
                icon_file: "cocktail-icon.png",
            },
        ];
    },
    get predefinedConfigs() {
        return [
            {
                name: "Restaurant",
                description: "Mobile for waiters, or on a laptop",
                function_name: "load_onboarding_pos_config_restaurant",
                icon_file: "/pos_restaurant/static/img/restaurant-icon.png",
            },
            {
                name: "Kiosk: self-order",
                description: "Let your customers order themselves",
                function_name: "load_onboarding_pos_config_kiosk",
                icon_file: "/pos_restaurant/static/img/cocktail-icon.png",
            },
            ...super.predefinedConfigs,
        ];
    },
});

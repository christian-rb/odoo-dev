/** @odoo-module **/
import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("test_revaluation_multi_company", {
    test: true, steps: () => [
        // Open the company switcher.
        { trigger: ".o_switch_company_menu > button", },
        // Switch company.
        { trigger: ".o_switch_company_menu .company_label:contains('Chicago')", },

        // Ensure the company is selected and Open Stock.
        {
            extra_trigger: ".o_switch_company_menu .oe_topbar_name:contains('Chicago')",
            trigger: "[data-menu-xmlid='stock.menu_stock_root']  .o_app_icon",
        },

        // Open stock valuation
        { trigger: "[data-menu-xmlid='stock.menu_warehouse_report']", },
        { trigger: "[data-menu-xmlid='stock_account.menu_valuation']", },

        // Add 20$ to the total value
        { trigger: "tr.o_group_has_content", },
        { trigger: "tr.o_group_has_content button", },

        {
            trigger: "div[name='added_value'] input",
            run: 'text 20',
        },
        { trigger: "button.btn.btn-primary[name='action_validate_revaluation']" },

        { trigger: "tr.o_group_has_content button", },
        {
            trigger: ".o_inventory_report_list_view",
            isCheck: true,
        }
    ]
});
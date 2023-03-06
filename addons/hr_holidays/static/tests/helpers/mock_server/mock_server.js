/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { MockServer } from "@web/../tests/helpers/mock_server";

patch(MockServer.prototype, {
    async _performRPC(route, args) {
        if (args.method === "get_mandatory_days_data") {
            return [];
        }
        if (args.method === "get_public_holidays_data") {
            return [];
        }
        if (args.method === "get_stress_days") {
            return {};
        }
        if (args.method === "get_mandatory_days") {
            return {};
        }
        return super._performRPC(...arguments);
    },
});

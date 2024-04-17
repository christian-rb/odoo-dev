/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { MockServer } from "@web/../tests/helpers/mock_server";

patch(MockServer.prototype, {
    /**
     * Simulate the creation of a custom appointment type
     * by receiving a list of slots.
     * @override
     */
    async _performRPC(route, args) {
        if (route === '/google_calendar/sync_data') {
            return Promise.resolve({status: 'no_new_event_from_google'});
        } else if (route === "/web/dataset/call_kw/res.users/get_show_all_calendars_filter") {
            return Promise.resolve(true);
        } else if (route === "/web/dataset/call_kw/res.users/set_show_all_calendars_filter") {
            return Promise.resolve();
        } else if (route === "/web/dataset/call_kw/res.users/get_show_own_calendar_filter") {
            return Promise.resolve(true);
        } else if (route === "/web/dataset/call_kw/res.users/set_show_own_calendar_filter") {
            return Promise.resolve();
        }
        return super._performRPC(...arguments);
    },
});

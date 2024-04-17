/** @odoo-module **/

import { listView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";

export class CalendarListModel extends listView.Model {
    setup(params, { action, dialog, notification, rpc, user, view, company }) {
        super.setup(...arguments);
    }

    /**
    * @override
    * Add the calendar view's selected attendees selected to the list view's domain.
    */
    async load(params = {}) {
        // Fetch from ORM the partner ids selected on calendar view and the Everybody's calendar filter state.
        const [selectedPartnerIds, isEveryoneFilterActive] = await Promise.all([
            this.orm.call("res.users", "get_selected_calendars_partner_ids", [[user.userId]]),
            this.orm.call("res.users", "get_show_all_calendars_filter", [[user.userId]]),
        ]);

        // Initialize empty domain when it is empty.
        if (!params.domain)
            params.domain = [];

        // When the "All Meetings" filter is off, add the selected attendees to the list view's domain.
        const allMeetingsFilter = params.domain.some(arr => arr.toString() === ['user_id', '!=', -1].toString());
        if (!isEveryoneFilterActive && !allMeetingsFilter)
            params.domain.push(["partner_ids", "in", selectedPartnerIds]);

        return super.load(params);
    }
}

export const CalendarListView = {
    ...listView,
    Model: CalendarListModel,
};

registry.category("views").add("calendar_list_view", CalendarListView);

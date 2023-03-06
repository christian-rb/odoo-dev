/** @odoo-module **/

import { AttendeeCalendarModel } from "@calendar/views/attendee_calendar/attendee_calendar_model";
import { serializeDate } from "@web/core/l10n/dates";
import { patch } from "@web/core/utils/patch";
patch(AttendeeCalendarModel.prototype, {
    setup() {
        super.setup(...arguments);
        this.mandatoryDays = {};
    },
    get employeeId() {
        return this.meta.context.employee_id ? this.meta.context.employee_id[0] : null;
    },
    async updateData(data) {
        await super.updateData(...arguments);
        this.mandatoryDays = await this.fetchDataList(data, "get_mandatory_days");
        data.mandatoryDaysList = await this.fetchDataList(data, "get_mandatory_days_data");
        data.unusualDaysList = await this.fetchDataList(data, "get_public_holidays_data");
    },
    async fetchDataList(data, method) {
        const attendeeFilters = data.filterSections.partner_ids.filters;
        const attendeeIds = attendeeFilters
            .filter((filter) => filter.type !== "all" && filter.value && filter.active)
            .map((filter) => filter.value);
        const all_attendees = attendeeFilters.some(
            (filter) => filter.type === "all" && filter.active
        );
        return this.orm.call("res.partner", method, [
            serializeDate(data.range.start, "datetime"),
            serializeDate(data.range.end, "datetime"),
            attendeeIds,
            all_attendees,
        ]);
    },
});

/** @odoo-module **/

import { AttendeeCalendarModel } from "@calendar/views/attendee_calendar/attendee_calendar_model";
import { serializeDate } from "@web/core/l10n/dates";
import { patch } from "@web/core/utils/patch";
patch(AttendeeCalendarModel.prototype, {
    setup () {
        super.setup(...arguments)
        this.data.workingHours = {};
    },

    get workingHours() {
        return this.data.workingHours;
    },

    get employeeId() {
        return this.meta.context.employee_id && this.meta.context.employee_id[0] || null;
    },

    async updateData(data) {
        await super.updateData(...arguments)
        data.workingHours = await this.fetchWorkingHours(data);
    },

    async fetchWorkingHours(data){
        if ((data.range.end - data.range.start)/(1000*3600*24) >= 28) {
            return false;
        }
        const attendeeFilters = data.filterSections.partner_ids;
        const activeAttendeeIds = attendeeFilters.filters
                .filter(filter => filter.type !== "all" && filter.value && filter.active)
                .map(filter => filter.value);
        const allFilter = attendeeFilters.filters.find(filter => filter.type === "all")
        const isEveryoneFilterActive = allFilter && allFilter.active || false;
        return this.orm.call("hr.employee", "get_working_hours_for_all_attendees", [
            this.employeeId,
            activeAttendeeIds,
            serializeDate(data.range.start),
            serializeDate(data.range.end),
            isEveryoneFilterActive]);
    }
})

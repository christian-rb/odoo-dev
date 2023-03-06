/** @odoo-module */
import { AttendeeCalendarYearRenderer } from "@calendar/views/attendee_calendar/year/attendee_calendar_year_renderer";
import { useCalendarPopover } from "@web/views/calendar/hooks";
import { TimeOffCalendarYearPopover } from "../year/calendar_year_popover";
import { useMandatoryDays } from "@hr_holidays/views/hooks";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
patch(AttendeeCalendarYearRenderer.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.mandatoryDaysList = [];
        this.mandatoryDays = useMandatoryDays(this.props);
        this.mandatoryDayPopover = useCalendarPopover(TimeOffCalendarYearPopover);
    },
    async onDateClick(info) {
        const is_mandatory_day = [...info.dayEl.classList].some((elClass) =>
            elClass.startsWith("hr_mandatory_day_")
        );
        this.mandatoryDayPopover.close();
        if (is_mandatory_day && !this.env.isSmall) {
            this.popover.close();
            const date = luxon.DateTime.fromISO(info.dateStr);
            const target = info.dayEl;
            const mandatory_days_data = this.props.model.data.mandatoryDaysList;
            mandatory_days_data.forEach((mandatory_day_data) => {
                mandatory_day_data["start"] = luxon.DateTime.fromISO(mandatory_day_data["start"]);
                mandatory_day_data["end"] = luxon.DateTime.fromISO(mandatory_day_data["end"]);
            });
            const mandatory_days_data_filtered = mandatory_days_data.filter(
                (elem) => elem["start"] <= date && elem["end"] >= date
            );
            const records = Object.values(this.props.model.records).filter((r) =>
                luxon.Interval.fromDateTimes(r.start.startOf("day"), r.end.endOf("day")).contains(
                    date
                )
            );
            const props = this.getPopoverProps(date, records);
            props["records"] = mandatory_days_data_filtered.concat(props["records"]);
            this.mandatoryDayPopover.open(target, props, "o_cw_popover");
        } else {
            super.onDateClick(...arguments);
        }
    },
    onDayRender(info) {
        this.mandatoryDays(info);
        this.mandatoryDaysList = this.mandatoryDays(info);
        super.onDayRender(info);
    },
});

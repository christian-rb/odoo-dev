/** @odoo-module */

import { AttendeeCalendarCommonRenderer } from "@calendar/views/attendee_calendar/common/attendee_calendar_common_renderer";
import { useMandatoryDays } from "@hr_holidays/views/hooks";
import { patch } from "@web/core/utils/patch";

patch(AttendeeCalendarCommonRenderer.prototype, {
    setup() {
        super.setup();
        this.mandatoryDays = useMandatoryDays(this.props);
    },
    get options() {
        return {
            ...super.options,
            eventOrder: function (event1, event2) {
                const prioritiesList = this.getEventPrioritiesList();
                const weight1 = prioritiesList[event1.extendedProps.type] || 0;
                const weight2 = prioritiesList[event2.extendedProps.type] || 0;
                console.log(weight1, weight2);
                if (weight1 > weight2) {
                    return -1;
                }
                if (weight1 < weight2) {
                    return 1;
                }
                return event1.title.localeCompare(event2.title);
            },
        };
    },
    getEventPrioritiesList() {
        const list = super.getEventPrioritiesList();
        return Object.assign(list, {
            publicHoliday: 90,
            mandatoryDay: 80,
        });
    },
    mapRecordsToEvents() {
        const events = super.mapRecordsToEvents(...arguments);
        this.props.model.data.mandatoryDaysList.forEach((day) => {
            events.push(...this.convertRecordToEvents(day, "mandatoryDay"));
        });
        this.props.model.data.unusualDaysList.forEach((day) => {
            events.push(...this.convertRecordToEvents(day, "publicHoliday"));
        });
        return events;
    },
    convertRecordToEvents(record, type) {
        const baseEvent = {
            id: record.id,
            title: record.title,
            start: record.start,
            start_date: luxon.DateTime.fromISO(record.start),
            end: luxon.DateTime.fromISO(record.end).plus({ day: 1 }).toISO(),
            end_date: luxon.DateTime.fromISO(record.end).plus({ day: 1 }),
            colorIndex: record.colorIndex,
            allDay: true,
            editable: false,
            type: type,
        };
        return [
            baseEvent,
            {
                ...baseEvent,
                rendering: "background",
            },
        ];
    },
    onClick(info) {
        const eventType = info.event._def.extendedProps.type;
        if (["publicHoliday", "mandatoryDay"].some((type) => type == eventType)) {
            return;
        }
        return super.onClick(...arguments);
    },
    onDblClick(info) {
        const eventType = info.event._def.extendedProps.type;
        if (["publicHoliday", "mandatoryDay"].some((type) => type == eventType)) {
            return;
        }
        return super.onDblClick(...arguments);
    },
    onEventRender(info) {
        const eventProps = info.event._def;
        const eventType = eventProps.extendedProps.type;
        if (!["publicHoliday", "mandatoryDay"].some((type) => type == eventType)) {
            return super.onEventRender(...arguments);
        }
        info.el.classList.add("o_specialday");
        if (eventProps.rendering !== "background") {
            return super.onEventRender(...arguments);
        }
        if (eventType === "mandatoryDay") {
            const colorCode =
                this.props.model.mandatoryDays[eventProps.extendedProps.start_date.toISODate()];
            info.el.classList.add(`hr_mandatory_day_${colorCode}`);
            return super.onEventRender(...arguments);
        }
        if (eventType === "publicHoliday") {
            info.el.classList.add("hr_public_holiday");
        }
        return super.onEventRender(...arguments);
    },
});

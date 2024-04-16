import { queryFirst } from "@odoo/hoot-dom";
import { createElement } from "@web/core/utils/xml";
import { Field } from "@web/views/fields/field";
import { contains } from "@web/../tests/web_test_helpers";

export const DEFAULT_DATE = luxon.DateTime.local(2021, 7, 16, 8, 0, 0, 0);

export const FAKE_RECORDS = {
    1: {
        id: 1,
        title: "1 day, all day in July",
        start: DEFAULT_DATE,
        isAllDay: true,
        end: DEFAULT_DATE,
    },
    2: {
        id: 2,
        title: "3 days, all day in July",
        start: DEFAULT_DATE.plus({ days: 2 }),
        isAllDay: true,
        end: DEFAULT_DATE.plus({ days: 4 }),
    },
    3: {
        id: 3,
        title: "1 day, all day in June",
        start: DEFAULT_DATE.plus({ months: -1 }),
        isAllDay: true,
        end: DEFAULT_DATE.plus({ months: -1 }),
    },
    4: {
        id: 4,
        title: "3 days, all day in June",
        start: DEFAULT_DATE.plus({ months: -1, days: 2 }),
        isAllDay: true,
        end: DEFAULT_DATE.plus({ months: -1, days: 4 }),
    },
    5: {
        id: 5,
        title: "Over June and July",
        start: DEFAULT_DATE.startOf("month").plus({ days: -2 }),
        isAllDay: true,
        end: DEFAULT_DATE.startOf("month").plus({ days: 2 }),
    },
};

export const FAKE_FILTER_SECTIONS = [
    {
        label: "Attendees",
        fieldName: "partner_ids",
        avatar: {
            model: "res.partner",
            field: "avatar_128",
        },
        hasAvatar: true,
        write: {
            model: "filter_partner",
            field: "partner_id",
        },
        canCollapse: true,
        canAddFilter: true,
        filters: [
            {
                type: "user",
                label: "Mitchell Admin",
                active: true,
                value: 3,
                colorIndex: 3,
                recordId: null,
                canRemove: false,
                hasAvatar: true,
            },
            {
                type: "all",
                label: "Everybody's calendar",
                active: false,
                value: "all",
                colorIndex: null,
                recordId: null,
                canRemove: false,
                hasAvatar: false,
            },
            {
                type: "record",
                label: "Brandon Freeman",
                active: true,
                value: 4,
                colorIndex: 4,
                recordId: 1,
                canRemove: true,
                hasAvatar: true,
            },
            {
                type: "record",
                label: "Marc Demo",
                active: false,
                value: 6,
                colorIndex: 6,
                recordId: 2,
                canRemove: true,
                hasAvatar: true,
            },
        ],
    },
    {
        label: "Users",
        fieldName: "user_id",
        avatar: {
            model: null,
            field: null,
        },
        hasAvatar: false,
        write: {
            model: null,
            field: null,
        },
        canCollapse: false,
        canAddFilter: false,
        filters: [
            {
                type: "record",
                label: "Brandon Freeman",
                active: false,
                value: 1,
                colorIndex: false,
                recordId: null,
                canRemove: true,
                hasAvatar: true,
            },
            {
                type: "record",
                label: "Marc Demo",
                active: false,
                value: 2,
                colorIndex: false,
                recordId: null,
                canRemove: true,
                hasAvatar: true,
            },
        ],
    },
];

export const FAKE_FIELDS = {
    id: { string: "Id", type: "integer" },
    user_id: { string: "User", type: "many2one", relation: "user", default: -1 },
    partner_id: {
        string: "Partner",
        type: "many2one",
        relation: "partner",
        related: "user_id.partner_id",
        default: 1,
    },
    name: { string: "Name", type: "char" },
    start_date: { string: "Start Date", type: "date" },
    stop_date: { string: "Stop Date", type: "date" },
    start: { string: "Start Datetime", type: "datetime" },
    stop: { string: "Stop Datetime", type: "datetime" },
    delay: { string: "Delay", type: "float" },
    allday: { string: "Is All Day", type: "boolean" },
    partner_ids: {
        string: "Attendees",
        type: "one2many",
        relation: "partner",
        default: [[6, 0, [1]]],
    },
    type: { string: "Type", type: "integer" },
    event_type_id: { string: "Event Type", type: "many2one", relation: "event_type" },
    color: { string: "Color", type: "integer", related: "event_type_id.color" },
};

export const FAKE_MODEL = {
    canCreate: true,
    canDelete: true,
    canEdit: true,
    date: DEFAULT_DATE,
    fieldMapping: {
        date_start: "start_date",
        date_stop: "stop_date",
        date_delay: "delay",
        all_day: "allday",
        color: "color",
    },
    fieldNames: ["start_date", "stop_date", "color", "delay", "allday", "user_id"],
    fields: FAKE_FIELDS,
    filterSections: FAKE_FILTER_SECTIONS,
    firstDayOfWeek: 0,
    isDateHidden: false,
    isTimeHidden: false,
    hasAllDaySlot: true,
    hasEditDialog: false,
    quickCreate: false,
    popoverFieldNodes: {
        name: Field.parseFieldNode(
            createElement("field", { name: "name" }),
            { event: { fields: FAKE_FIELDS } },
            "event",
            "calendar"
        ),
    },
    activeFields: {
        name: {
            context: "{}",
            invisible: false,
            readonly: false,
            required: false,
            onChange: false,
        },
    },
    rangeEnd: DEFAULT_DATE.endOf("month"),
    rangeStart: DEFAULT_DATE.startOf("month"),
    records: FAKE_RECORDS,
    resModel: "event",
    scale: "month",
    scales: ["day", "week", "month", "year"],
    unusualDays: [],
    load() {},
    createFilter() {},
    createRecord() {},
    unlinkFilter() {},
    unlinkRecord() {},
    updateFilter() {},
    updateRecord() {},
};

// DOM Utils
//------------------------------------------------------------------------------

// export function findPickedDate(target) {
//     return target.querySelector(".o_datetime_picker .o_selected");
// }

// export async function pickDate(target, date) {
//     const day = date.split("-")[2];
//     const iDay = parseInt(day, 10) - 1;
//     const el = target.querySelectorAll(`.o_datetime_picker .o_date_item_cell:not(.o_out_of_range)`)[
//         iDay
//     ];
//     el.scrollIntoView();
//     await click(el);
// }

// export function expandCalendarView(target) {
//     // Expends Calendar view and FC too
//     let tmpElement = target.querySelector(".fc");
//     do {
//         tmpElement = tmpElement.parentElement;
//         tmpElement.classList.add("h-100");
//     } while (!tmpElement.classList.contains("o_view_controller"));
// }

export function findAllDaySlot(date) {
    return queryFirst(`.fc-daygrid-body .fc-day[data-date="${date}"]`);
}

/**
 * @param {string} date
 * @returns {HTMLElement}
 */
export function findDateCell(date) {
    return queryFirst(`.fc-day[data-date="${date}"]`);
}

export function findEvent(eventId) {
    return queryFirst(`.o_event[data-event-id="${eventId}"]`);
}

export function findDateCol(date) {
    return queryFirst(`.fc-col-header-cell.fc-day[data-date="${date}"]`);
}

export function findTimeRow(time) {
    return queryFirst(`.fc-timegrid-slot[data-time="${time}"]`);
}

// export async function triggerEventForCalendar(el, type, position = {}) {
//     const rect = el.getBoundingClientRect();
//     const x = position.x || rect.x + rect.width / 2;
//     const y = position.y || rect.y + rect.height / 2;
//     const attrs = {
//         which: 1,
//         clientX: x,
//         clientY: y,
//     };
//     await triggerEvent(el, null, type, attrs);
// }

// export async function clickAllDaySlot(target, date) {
//     const el = findAllDaySlot(target, date);
//     await scrollTo(el);
//     await triggerEventForCalendar(el, "mousedown");
//     await triggerEventForCalendar(el, "mouseup");
//     await animationFrame();
// }

export async function clickDate(date) {
    const cell = findDateCell(date);
    cell.scrollIntoView({ behavior: "instant" });
    await contains(cell).click();
}

// export async function clickEvent(target, eventId) {
//     const el = findEvent(target, eventId);
//     await scrollTo(el);
//     await click(el);
//     await animationFrame();
// }

// export async function selectTimeRange(target, startDateTime, endDateTime) {
//     const [startDate, startTime] = startDateTime.split(" ");
//     const [endDate, endTime] = endDateTime.split(" ");

//     const startCol = findDateCol(target, startDate);
//     const endCol = findDateCol(target, endDate);
//     const startRow = findTimeRow(target, startTime);
//     const endRow = findTimeRow(target, endTime);

//     await scrollTo(startRow);
//     const startColRect = startCol.getBoundingClientRect();
//     const startRowRect = startRow.getBoundingClientRect();

//     await triggerEventForCalendar(startRow, "mousedown", {
//         x: startColRect.x + startColRect.width / 2,
//         y: startRowRect.y + 2,
//     });

//     await scrollTo(endRow, false);
//     const endColRect = endCol.getBoundingClientRect();
//     const endRowRect = endRow.getBoundingClientRect();

//     await triggerEventForCalendar(endRow, "mousemove", {
//         x: endColRect.x + endColRect.width / 2,
//         y: endRowRect.y - 2,
//     });
//     await triggerEventForCalendar(endRow, "mouseup", {
//         x: endColRect.x + endColRect.width / 2,
//         y: endRowRect.y - 2,
//     });
//     await animationFrame();
// }

export async function selectDateRange(startDate, endDate) {
    const startCell = findDateCell(startDate);
    const endCell = findDateCell(endDate);

    startCell.scrollIntoView({ behavior: "instant" });
    const { drop, moveTo } = await contains(startCell).drag();
    await moveTo(endCell);
    await drop();
}

// export async function selectAllDayRange(target, startDate, endDate) {
//     const start = findAllDaySlot(target, startDate);
//     const end = findAllDaySlot(target, endDate);
//     await scrollTo(start);
//     await triggerEventForCalendar(start, "mousedown");
//     await scrollTo(end);
//     await triggerEventForCalendar(end, "mousemove");
//     await triggerEventForCalendar(end, "mouseup");
//     await animationFrame();
// }

// export async function moveEventToDate(target, eventId, date, options = {}) {
//     const event = findEvent(target, eventId);
//     const cell = findDateCell(target, date);

//     await scrollTo(event);
//     await triggerEventForCalendar(event, "mousedown");

//     await scrollTo(cell);
//     await triggerEventForCalendar(cell, "mousemove");

//     if (!options.disableDrop) {
//         await triggerEventForCalendar(cell, "mouseup");
//     }
//     await animationFrame();
// }

// export async function moveEventToTime(target, eventId, dateTime) {
//     const event = findEvent(target, eventId);
//     const [date, time] = dateTime.split(" ");

//     const col = findDateCol(target, date);
//     const row = findTimeRow(target, time);

//     // Find event position
//     await scrollTo(event);
//     const eventRect = event.getBoundingClientRect();
//     const eventPos = {
//         x: eventRect.x + eventRect.width / 2,
//         y: eventRect.y,
//     };

//     await triggerEventForCalendar(event, "mousedown", eventPos);

//     // Find target position
//     await scrollTo(row, false);
//     const colRect = col.getBoundingClientRect();
//     const rowRect = row.getBoundingClientRect();
//     const toPos = {
//         x: colRect.x + colRect.width / 2,
//         y: rowRect.y - 1,
//     };

//     await triggerEventForCalendar(row, "mousemove", toPos);
//     await triggerEventForCalendar(row, "mouseup", toPos);
//     await animationFrame();
// }

// export async function moveEventToAllDaySlot(target, eventId, date) {
//     const event = findEvent(target, eventId);
//     const slot = findAllDaySlot(target, date);

//     // Find event position
//     await scrollTo(event);
//     const eventRect = event.getBoundingClientRect();
//     const eventPos = {
//         x: eventRect.x + eventRect.width / 2,
//         y: eventRect.y,
//     };
//     await triggerEventForCalendar(event, "mousedown", eventPos);

//     // Find target position
//     await scrollTo(slot);
//     const slotRect = slot.getBoundingClientRect();
//     const toPos = {
//         x: slotRect.x + slotRect.width / 2,
//         y: slotRect.y - 1,
//     };
//     await triggerEventForCalendar(slot, "mousemove", toPos);
//     await triggerEventForCalendar(slot, "mouseup", toPos);
//     await animationFrame();
// }

// export async function resizeEventToTime(target, eventId, dateTime) {
//     const event = findEvent(target, eventId);
//     const [date, time] = dateTime.split(" ");

//     const col = findDateCol(target, date);
//     const row = findTimeRow(target, time);

//     // Find event position
//     await scrollTo(event);
//     await triggerEventForCalendar(event, "mouseover");

//     // Find event resizer
//     const resizer = event.querySelector(".fc-event-resizer-end");
//     resizer.style.display = "block";
//     resizer.style.width = "100%";
//     resizer.style.height = "1em";
//     resizer.style.bottom = "0";
//     const resizerRect = resizer.getBoundingClientRect();
//     const resizerPos = {
//         x: resizerRect.x + resizerRect.width / 2,
//         y: resizerRect.y + resizerRect.height / 2,
//     };
//     await triggerEventForCalendar(resizer, "mousedown", resizerPos);

//     // Find target position
//     await scrollTo(row, false);
//     const colRect = col.getBoundingClientRect();
//     const rowRect = row.getBoundingClientRect();
//     const toPos = {
//         x: colRect.x + colRect.width / 2,
//         y: rowRect.y - 1,
//     };

//     await triggerEventForCalendar(row, "mousemove", toPos);
//     await triggerEventForCalendar(row, "mouseup", toPos);
//     await animationFrame();
// }

// export async function changeScale(target, scale) {
//     await click(target, `.o_view_scale_selector .scale_button_selection`);
//     await click(target, `.o-dropdown--menu .o_scale_button_${scale}`);
//     await animationFrame();
// }

// export async function navigate(target, direction) {
//     await click(target, `.o_calendar_navigation_buttons .o_calendar_button_${direction}`);
// }

// export function findFilterPanelSection(target, sectionName) {
//     return target.querySelector(`.o_calendar_filter[data-name="${sectionName}"]`);
// }

// export function findFilterPanelFilter(target, sectionName, filterValue) {
//     return findFilterPanelSection(target, sectionName).querySelector(
//         `.o_calendar_filter_item[data-value="${filterValue}"]`
//     );
// }

// export function findFilterPanelSectionFilter(target, sectionName) {
//     return findFilterPanelSection(target, sectionName).querySelector(
//         `.o_calendar_filter_items_checkall`
//     );
// }

// export async function toggleFilter(target, sectionName, filterValue) {
//     const el = findFilterPanelFilter(target, sectionName, filterValue).querySelector(`input`);
//     await scrollTo(el);
//     await click(el);
// }

// export async function toggleSectionFilter(target, sectionName) {
//     const el = findFilterPanelSectionFilter(target, sectionName).querySelector(`input`);
//     await scrollTo(el);
//     await click(el);
// }

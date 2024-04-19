import { beforeEach, expect, test } from "@odoo/hoot";
import { mockDate } from "@odoo/hoot-mock";
import {
    contains,
    defineModels,
    fields,
    models,
    mountView,
    serverState,
} from "@web/../tests/web_test_helpers";
import { changeScale, removeFilter, toggleFilter } from "./calendar_test_helpers";
import { queryAllTexts } from "@odoo/hoot-dom";

class Event extends models.Model {
    name = fields.Char();
    type_id = fields.Many2one({ relation: "event.type" });
    start_date = fields.Date({ compute: "_compute_start_date", store: true });
    stop_date = fields.Date({ compute: "_compute_stop_date", store: true });
    start = fields.Datetime();
    stop = fields.Datetime();
    delay = fields.Float();
    is_all_day = fields.Boolean();
    user_id = fields.Many2one({ relation: "calendar.users", default: serverState.userId });
    partner_id = fields.Many2one({ relation: "calendar.partner", default: 1 });
    attendee_ids = fields.One2many({ relation: "calendar.partner", default: [[6, 0, [1]]] });
    color = fields.Integer({ related: "type_id.color" });
    is_hatched = fields.Boolean();
    is_striked = fields.Boolean();

    check_access_rights() {
        return true;
    }

    _compute_start_date() {
        for (const record of this) {
            record.start_date = record.start && record.start.split(" ")[0];
        }
    }

    _compute_stop_date() {
        for (const record of this) {
            record.stop_date = record.stop && record.stop.split(" ")[0];
        }
    }

    _records = [
        {
            id: 1,
            name: "event 1",
            start: "2016-12-11 00:00:00",
            stop: "2016-12-11 00:00:00",
            user_id: serverState.userId,
            partner_id: 1,
            attendee_ids: [1, 2, 3],
        },
        {
            id: 2,
            name: "event 2",
            start: "2016-12-12 10:55:05",
            stop: "2016-12-12 14:55:05",
            user_id: serverState.userId,
            partner_id: 1,
            attendee_ids: [1, 2],
        },
        {
            id: 3,
            name: "event 3",
            start: "2016-12-12 15:55:05",
            stop: "2016-12-12 16:55:05",
            user_id: 4,
            partner_id: 4,
            attendee_ids: [1],
            is_hatched: true,
        },
        {
            id: 4,
            name: "event 4",
            start: "2016-12-14 15:55:05",
            stop: "2016-12-14 18:55:05",
            is_all_day: true,
            user_id: serverState.userId,
            partner_id: 1,
            attendee_ids: [1],
            is_striked: true,
        },
        {
            id: 5,
            name: "event 5",
            start: "2016-12-13 15:55:05",
            stop: "2016-12-20 18:55:05",
            user_id: 4,
            partner_id: 4,
            attendee_ids: [2, 3],
            is_hatched: true,
        },
        {
            id: 6,
            name: "event 6",
            start: "2016-12-18 08:00:00",
            stop: "2016-12-18 09:00:00",
            user_id: serverState.userId,
            partner_id: 1,
            attendee_ids: [3],
            is_hatched: true,
        },
        {
            id: 7,
            name: "event 7",
            start: "2016-11-14 08:00:00",
            stop: "2016-11-16 17:00:00",
            user_id: serverState.userId,
            partner_id: 1,
            attendee_ids: [2],
        },
    ];
}

class EventType extends models.Model {
    _name = "event.type";

    name = fields.Char();
    color = fields.Integer();

    _records = [
        { id: 1, name: "Event Type 1", color: 1 },
        { id: 2, name: "Event Type 2", color: 2 },
        { id: 3, name: "Event Type 3 (color 4)", color: 4 },
    ];
}

class CalendarUsers extends models.Model {
    _name = "calendar.users";

    name = fields.Char();
    partner_id = fields.Many2one({ relation: "calendar.partner" });
    image = fields.Char();

    _records = [
        { id: serverState.userId, name: "user 1", partner_id: 1 },
        { id: 4, name: "user 4", partner_id: 4 },
    ];
}

class CalendarPartner extends models.Model {
    _name = "calendar.partner";

    name = fields.Char();
    image = fields.Char();

    _records = [
        { id: 1, name: "partner 1", image: "AAA" },
        { id: 2, name: "partner 2", image: "BBB" },
        { id: 3, name: "partner 3", image: "CCC" },
        { id: 4, name: "partner 4", image: "DDD" },
    ];
}

class FilterPartner extends models.Model {
    _name = "filter.partner";

    user_id = fields.Many2one({ relation: "calendar.users" });
    partner_id = fields.Many2one({ relation: "calendar.partner" });
    is_checked = fields.Boolean();

    _records = [
        { id: 1, user_id: serverState.userId, partner_id: 1, is_checked: true },
        { id: 2, user_id: serverState.userId, partner_id: 2, is_checked: true },
        { id: 3, user_id: 4, partner_id: 3, is_checked: false },
    ];
}

defineModels([Event, EventType, CalendarUsers, CalendarPartner, FilterPartner]);

beforeEach(() => {
    mockDate("2016-12-12T08:00:00");
});

test(`simple calendar rendering`, async () => {
    Event._records.push(
        {
            id: 8,
            user_id: serverState.userId,
            partner_id: false,
            name: "event 7",
            start: "2016-12-18 09:00:00",
            stop: "2016-12-18 10:00:00",
            attendee_ids: [2],
        },
        {
            id: 9,
            user_id: serverState.userId,
            partner_id: false,
            name: "event 8",
            start: "2016-12-11 05:15:00",
            stop: "2016-12-11 05:30:00",
            attendee_ids: [1, 2, 3],
            delay: 0.25,
        }
    );

    await mountView({
        resModel: "event",
        type: "calendar",
        arch: `
            <calendar event_open_popup="1" date_start="start" date_stop="stop" all_day="is_all_day" mode="week" attendee="attendee_ids" color="partner_id" date_delay="delay">
                <filter name="user_id" avatar_field="image" />
                <field name="attendee_ids" write_model="filter.partner" write_field="partner_id" />
                <field name="partner_id" filters="1" invisible="1" />
                <field name="delay" invisible="1"/>
            </calendar>
        `,
    });

    // test events in different scale
    expect(`.o_calendar_renderer .fc-view`).toHaveCount(1);
    expect(`.fc-event`).toHaveCount(0, {
        message: "By default, only the events of the current user are displayed (0 in this case)",
    });

    await toggleFilter("attendee_ids", "all");
    expect(`.fc-event`).toHaveCount(6, {
        message: "should display 6 events on the week (4 event + 1 is_all_day + 1 >24h is_all_day)",
    });
    expect(`.o_event_oneliner`).toHaveCount(1, {
        message: "should contain 1 oneliner event (the one we add)",
    });

    await changeScale("day");
    expect(`.fc-event`).toHaveCount(2);
    expect(`.o_calendar_sidebar .o_datetime_picker .o_highlight_start`).toHaveCount(1);
    expect(`.o_calendar_sidebar .o_datetime_picker .o_highlight_end`).toHaveCount(1);

    await changeScale("month");
    await toggleFilter("attendee_ids", "all");
    await toggleFilter("attendee_ids", "1");
    await toggleFilter("attendee_ids", "2");
    expect(`.fc-event`).toHaveCount(8, {
        message:
            "should display 7 events on the month (6 events + 2 week event - 1 'event 6' is filtered + 1 'Undefined event')",
    });

    // test filters
    expect(`.o_calendar_sidebar .o_calendar_filter`).toHaveCount(2);
    expect(`.o_calendar_filter:eq(1)`).toBeDisplayed();
    expect(`.o_calendar_filter:eq(1) .o_calendar_filter_item`).toHaveCount(3);

    expect(`.o_calendar_filter:eq(1) .o_calendar_filter_item:eq(-1)`).not.toHaveAttribute(
        "data-value"
    );
    expect(`.o_calendar_filter:eq(1) .o_calendar_filter_item:eq(-1)`).toHaveText("Undefined");
    expect(`.o_calendar_filter:eq(1) .o_calendar_filter_item:eq(-1) label img`).toHaveCount(0);

    expect(`.o_calendar_filter:eq(0)`).toBeDisplayed();
    expect(`.o_calendar_filter:eq(0) .o_calendar_filter_item`).toHaveCount(3);
    expect(`.o_calendar_filter:eq(0) .o-autocomplete`).toHaveCount(1);

    await toggleFilter("attendee_ids", "1");
    expect(`.fc-event`).toHaveCount(6);

    await toggleFilter("attendee_ids", "2");
    expect(`.fc-event`).toHaveCount(0);

    // test search bar in filter
    await contains(`.o_calendar_sidebar input[type=text]`).click();
    expect(`.dropdown-item`).toHaveCount(2);
    expect(queryAllTexts`.dropdown-item`).toEqual(["partner 3", "partner 4"]);

    await contains(`.dropdown-item:eq(0)`).click();
    expect(`.o_calendar_filter:eq(0) .o_calendar_filter_item`).toHaveCount(4);

    await contains(`.o_calendar_sidebar input[type=text]`).click();
    expect(`.dropdown-item`).toHaveCount(1);
    expect(`.dropdown-item`).toHaveText("partner 4");

    await removeFilter("attendee_ids", "2");
    expect(`.o_calendar_filter:eq(0) .o_calendar_filter_item`).toHaveCount(3);
});

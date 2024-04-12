import { expect, test } from "@odoo/hoot";
import { mountWithCleanup } from "../../web_test_helpers";
import { CalendarCommonPopover } from "@web/views/calendar/calendar_common/calendar_common_popover";
import { DEFAULT_DATE, FAKE_MODEL } from "./calendar_test_helpers";
import { click } from "@odoo/hoot-dom";

function fakeRecord(data = {}) {
    return {
        id: 5,
        title: "Meeting",
        isAllDay: false,
        start: DEFAULT_DATE,
        end: DEFAULT_DATE.plus({ hours: 3, minutes: 15 }),
        colorIndex: 0,
        isTimeHidden: false,
        rawRecord: {
            name: "Meeting",
        },
        ...data,
    };
}

function fakeProps(props = {}) {
    return {
        model: FAKE_MODEL,
        record: fakeRecord(),
        createRecord() {},
        deleteRecord() {},
        editRecord() {},
        close() {},
        ...props,
    };
}

test(`mount a CalendarCommonPopover`, async () => {
    await mountWithCleanup(CalendarCommonPopover, {
        props: fakeProps({}),
    });
    expect(`.popover-header`).toHaveCount(1);
    expect(`.popover-header`).toHaveText("Meeting");
    expect(`.list-group`).toHaveCount(2);
    expect(`.list-group.o_cw_popover_fields_secondary`).toHaveCount(1);
    expect(`.card-footer .o_cw_popover_edit`).toHaveCount(1);
    expect(`.card-footer .o_cw_popover_delete`).toHaveCount(1);
});

test(`date duration: is all day and is same day`, async () => {
    await mountWithCleanup(CalendarCommonPopover, {
        props: fakeProps({
            record: fakeRecord({ isAllDay: true, isTimeHidden: true }),
        }),
    });
    expect(`.list-group:eq(0)`).toHaveText("July 16, 2021");
});

test(`date duration: is all day and two days duration`, async () => {
    await mountWithCleanup(CalendarCommonPopover, {
        props: fakeProps({
            record: fakeRecord({
                end: DEFAULT_DATE.plus({ days: 1 }),
                isAllDay: true,
                isTimeHidden: true,
            }),
        }),
    });
    expect(`.list-group:eq(0)`).toHaveText("July 16-17, 2021 2 days");
});

test(`time duration: 1 hour diff`, async () => {
    await mountWithCleanup(CalendarCommonPopover, {
        props: fakeProps({
            record: fakeRecord({ end: DEFAULT_DATE.plus({ hours: 1 }) }),
            model: { ...FAKE_MODEL, isDateHidden: true },
        }),
    });
    expect(`.list-group:eq(0)`).toHaveText("08:00 - 09:00 (1 hour)");
});

test(`time duration: 2 hours diff`, async () => {
    await mountWithCleanup(CalendarCommonPopover, {
        props: fakeProps({
            record: fakeRecord({ end: DEFAULT_DATE.plus({ hours: 2 }) }),
            model: { ...FAKE_MODEL, isDateHidden: true },
        }),
    });
    expect(`.list-group:eq(0)`).toHaveText("08:00 - 10:00 (2 hours)");
});

test(`time duration: 1 minute diff`, async () => {
    await mountWithCleanup(CalendarCommonPopover, {
        props: fakeProps({
            record: fakeRecord({ end: DEFAULT_DATE.plus({ minutes: 1 }) }),
            model: { ...FAKE_MODEL, isDateHidden: true },
        }),
    });
    expect(`.list-group:eq(0)`).toHaveText("08:00 - 08:01 (1 minute)");
});

test(`time duration: 2 minutes diff`, async () => {
    await mountWithCleanup(CalendarCommonPopover, {
        props: fakeProps({
            record: fakeRecord({ end: DEFAULT_DATE.plus({ minutes: 2 }) }),
            model: { ...FAKE_MODEL, isDateHidden: true },
        }),
    });
    expect(`.list-group:eq(0)`).toHaveText("08:00 - 08:02 (2 minutes)");
});

test(`time duration: 3 hours and 15 minutes diff`, async () => {
    await mountWithCleanup(CalendarCommonPopover, {
        props: fakeProps({
            model: { ...FAKE_MODEL, isDateHidden: true },
        }),
    });
    expect(`.list-group:eq(0)`).toHaveText("08:00 - 11:15 (3 hours, 15 minutes)");
});

test(`isDateHidden is true`, async () => {
    await mountWithCleanup(CalendarCommonPopover, {
        props: fakeProps({
            model: { ...FAKE_MODEL, isDateHidden: true },
        }),
    });
    expect(`.list-group:eq(0)`).toHaveText("08:00 - 11:15 (3 hours, 15 minutes)");
});

test(`isDateHidden is false`, async () => {
    await mountWithCleanup(CalendarCommonPopover, {
        props: fakeProps({
            model: { ...FAKE_MODEL, isDateHidden: false },
        }),
    });
    expect(`.list-group:eq(0)`).toHaveText("July 16, 2021\n08:00 - 11:15 (3 hours, 15 minutes)");
});

test(`isTimeHidden is true`, async () => {
    await mountWithCleanup(CalendarCommonPopover, {
        props: fakeProps({
            record: fakeRecord({ isTimeHidden: true }),
        }),
    });
    expect(`.list-group:eq(0)`).toHaveText("July 16, 2021");
});

test(`isTimeHidden is false`, async () => {
    await mountWithCleanup(CalendarCommonPopover, {
        props: fakeProps({
            record: fakeRecord({ isTimeHidden: false }),
        }),
    });
    expect(`.list-group:eq(0)`).toHaveText("July 16, 2021\n08:00 - 11:15 (3 hours, 15 minutes)");
});

test(`canDelete is true`, async () => {
    await mountWithCleanup(CalendarCommonPopover, {
        props: fakeProps({
            model: { ...FAKE_MODEL, canDelete: true },
        }),
    });
    expect(`.o_cw_popover_delete`).toHaveCount(1);
});

test(`canDelete is false`, async () => {
    await mountWithCleanup(CalendarCommonPopover, {
        props: fakeProps({
            model: { ...FAKE_MODEL, canDelete: false },
        }),
    });
    expect(`.o_cw_popover_delete`).toHaveCount(0);
});

test(`click on delete button`, async () => {
    await mountWithCleanup(CalendarCommonPopover, {
        props: fakeProps({
            model: { ...FAKE_MODEL, canDelete: true },
            deleteRecord: () => expect.step("delete"),
        }),
    });
    click(`.o_cw_popover_delete`);
    expect(["delete"]).toVerifySteps();
});

test(`click on edit button`, async () => {
    await mountWithCleanup(CalendarCommonPopover, {
        props: fakeProps({
            editRecord: () => expect.step("edit"),
        }),
    });
    click(`.o_cw_popover_edit`);
    expect(["edit"]).toVerifySteps();
});

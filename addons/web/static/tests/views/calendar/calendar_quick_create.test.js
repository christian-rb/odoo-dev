import { expect, test } from "@odoo/hoot";
import { waitFor } from "@odoo/hoot-dom";
import { getService, mountWithCleanup } from "@web/../tests/web_test_helpers";
import { FAKE_MODEL } from "./calendar_test_helpers";

import { MainComponentsContainer } from "@web/core/main_components_container";
import { CalendarQuickCreate } from "@web/views/calendar/quick_create/calendar_quick_create";

const FAKE_PROPS = {
    model: FAKE_MODEL,
    record: {},
    editRecord() {},
};

test(`mount a CalendarQuickCreate`, async () => {
    await mountWithCleanup(MainComponentsContainer);
    getService("dialog").add(CalendarQuickCreate, FAKE_PROPS);
    await waitFor(`.o_dialog`);

    expect(`.o-calendar-quick-create`).toHaveCount(1);
    expect(`.o_dialog .modal-sm`).toHaveCount(1);
    expect(`.modal-title`).toHaveText("New Event");
    expect(`input[name="title"]`).toBeFocused();
    expect(`.o-calendar-quick-create--create-btn`).toHaveCount(1);
    expect(`.o-calendar-quick-create--edit-btn`).toHaveCount(1);
    expect(`.o-calendar-quick-create--cancel-btn`).toHaveCount(1);
});

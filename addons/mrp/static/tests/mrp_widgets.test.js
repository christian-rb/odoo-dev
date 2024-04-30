import { describe, expect, test } from "@odoo/hoot";
import { defineModels, fields, webModels } from "@web/../tests/web_test_helpers";
import { mailModels, openFormView, start, startServer } from "@mail/../tests/mail_test_helpers";
import { busModels } from "@bus/../tests/bus_test_helpers";
import { DEFAULT_MAIL_VIEW_ID } from "@mail/../tests/mock_server/mock_models/constants";

describe.current.tags("desktop");

class ResFake extends mailModels.ResFake {
    _views = {
        [`form,${DEFAULT_MAIL_VIEW_ID}`]: /* xml */ `
            <form>
                <field name="duration" widget="mrp_timer" readonly="1"/>
            </form>`,
    }
    duration = fields.Float({ string: "duration" });
}
defineModels({ ...webModels, ...busModels, ...mailModels, ResFake });

test("ensure the rendering is based on minutes and seconds", async () => {
    const pyEnv = await startServer();
    const fakeId = pyEnv["res.fake"].create({ duration: 150.5 });
    await start();
    await openFormView("res.fake", fakeId);
    expect(document.querySelector(".o_field_mrp_timer").textContent).toBe("150:30");
});

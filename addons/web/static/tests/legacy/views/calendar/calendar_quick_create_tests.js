/* eslint-disable */
/** @odoo-module alias=@web/../tests/views/calendar/calendar_quick_create_tests default=false */

import { CalendarQuickCreate } from "@web/views/calendar/quick_create/calendar_quick_create";
import { click, getFixture } from "../../helpers/utils";
import { makeEnv, makeFakeModel, mountComponent } from "./helpers";

let target;

async function start(params = {}) {
    const { services, props, model: modelParams } = params;
    const env = await makeEnv(services);
    env.dialogData = {
        isActive: true,
        close() {},
    };
    const model = makeFakeModel(modelParams);
    return await mountComponent(CalendarQuickCreate, env, {
        model,
        record: {},
        close() {},
        editRecord() {},
        ...props,
    });
}

QUnit.module("CalendarView - QuickCreate", ({ beforeEach }) => {
    beforeEach(() => {
        target = getFixture();
    });

    QUnit.test("mount a CalendarQuickCreate", async (assert) => {
        await start({});
        expect(`.o-calendar-quick-create`).tohaveCount(1);
        expect(`.o_dialog .modal-sm`).tohaveCount(1);
        assert.strictEqual(target.querySelector(".modal-title").textContent, "New Event");
        assert.strictEqual(target.querySelector(`input[name="title"]`), document.activeElement);
        expect(`.o-calendar-quick-create--create-btn`).tohaveCount(1);
        expect(`.o-calendar-quick-create--edit-btn`).tohaveCount(1);
        expect(`.o-calendar-quick-create--cancel-btn`).tohaveCount(1);
    });

    QUnit.test("click on create button", async (assert) => {
        assert.expect(2);
        await start({
            props: {
                close: () => assert.step("close"),
            },
            model: {
                createRecord: () => assert.step("create"),
            },
        });
        await contains(`.o-calendar-quick-create--create-btn`).click();
        expect([]).toVerifySteps();
        assert.hasClass(target.querySelector("input[name=title]"), "o_field_invalid");
    });

    QUnit.test("click on create button (with name)", async (assert) => {
        assert.expect(4);
        await start({
            props: {
                close: () => assert.step("close"),
            },
            model: {
                createRecord(record) {
                    assert.step("create");
                    assert.strictEqual(record.title, "TEST");
                },
            },
        });

        const input = target.querySelector(".o-calendar-quick-create--input");
        input.value = "TEST";

        await contains(`.o-calendar-quick-create--create-btn`).click();
        expect(["create", "close"]).toVerifySteps();
    });

    QUnit.test("click on edit button", async (assert) => {
        assert.expect(3);
        await start({
            props: {
                close: () => assert.step("close"),
                editRecord: () => assert.step("edit"),
            },
        });
        await contains(`.o-calendar-quick-create--edit-btn`).click();
        expect(["edit", "close"]).toVerifySteps();
    });

    QUnit.test("click on edit button (with name)", async (assert) => {
        assert.expect(4);
        await start({
            props: {
                close: () => assert.step("close"),
                editRecord(record) {
                    assert.step("edit");
                    assert.strictEqual(record.title, "TEST");
                },
            },
        });

        const input = target.querySelector(".o-calendar-quick-create--input");
        input.value = "TEST";

        await contains(`.o-calendar-quick-create--edit-btn`).click();
        expect(["edit", "close"]).toVerifySteps();
    });

    QUnit.test("click on cancel button", async (assert) => {
        assert.expect(2);
        await start({
            props: {
                close: () => assert.step("close"),
            },
        });
        await contains(`.o-calendar-quick-create--cancel-btn`).click();
        expect(["close"]).toVerifySteps();
    });

    QUnit.test("check default title", async (assert) => {
        assert.expect(1);
        await start({
            props: {
                title: "Example Title",
            },
        });

        const input = target.querySelector(".o-calendar-quick-create--input");
        assert.strictEqual(input.value, "Example Title");
    });
});

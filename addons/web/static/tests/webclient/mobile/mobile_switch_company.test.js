import { beforeEach, describe, expect, test } from "@odoo/hoot";
import { animationFrame, runAllTimers } from "@odoo/hoot-mock";
import { queryAllTexts } from "@odoo/hoot-dom";
import {
    contains,
    getService,
    mountWithCleanup,
    patchWithCleanup,
} from "@web/../tests/web_test_helpers";

import { browser } from "@web/core/browser/browser";
import { router } from "@web/core/browser/router";
import { session } from "@web/session";
import { MobileSwitchCompanyMenu } from "@web/webclient/burger_menu/mobile_switch_company_menu/mobile_switch_company_menu";

const ORIGINAL_TOGGLE_DELAY = MobileSwitchCompanyMenu.toggleDelay;

async function createSwitchCompanyMenu(routerParams = {}, toggleDelay = 0) {
    patchWithCleanup(MobileSwitchCompanyMenu, { toggleDelay });
    if (routerParams.onPushState) {
        const pushState = browser.history.pushState;
        patchWithCleanup(browser.history, {
            pushState(state, title, url) {
                pushState.apply(browser.history, ...arguments);
                if (routerParams.onPushState) {
                    routerParams.onPushState(url);
                }
            },
        });
    }
    await mountWithCleanup(MobileSwitchCompanyMenu);
}

describe.current.tags("mobile");

async function toggle(index) {
    await contains(`[data-company-id] [role=menuitemcheckbox]:eq(${index})`).click();
}

async function confirm() {
    await contains(".o_switch_company_menu_buttons button:first").click();
}

beforeEach(() => {
    patchWithCleanup(session.user_companies, {
        allowed_companies: {
            1: { id: 1, name: "Hermit", parent_id: false, child_ids: [] },
            2: { id: 2, name: "Herman's", parent_id: false, child_ids: [] },
            3: { id: 3, name: "Heroes TM", parent_id: false, child_ids: [] },
        },
        current_company: 1,
    });
});

test("basic rendering", async () => {
    await createSwitchCompanyMenu();

    expect(".o_burger_menu_companies").toHaveProperty("tagName", "DIV");
    expect(".o_burger_menu_companies").toHaveClass("o_burger_menu_companies");
    expect("[data-company-id]").toHaveCount(3);
    expect(".log_into").toHaveCount(3);
    expect(".fa-check-square").toHaveCount(1);
    expect(".fa-square-o").toHaveCount(2);

    expect(".o_switch_company_item:eq(0)").toHaveText("Hermit");
    expect(".o_switch_company_item:eq(0)").toHaveClass("alert-secondary");
    expect(".o_switch_company_item:eq(1)").toHaveText("Herman's");
    expect(".o_switch_company_item:eq(2)").toHaveText("Heroes TM");

    expect(".o_switch_company_item i:eq(0)").toHaveClass("fa-check-square");
    expect(".o_switch_company_item i:eq(1)").toHaveClass("fa-square-o");
    expect(".o_switch_company_item i:eq(2)").toHaveClass("fa-square-o");

    expect(".o_burger_menu_companies").toHaveText("Companies\nHermit\nHerman's\nHeroes TM");
});

test("companies can be toggled: toggle a second company", async () => {
    function onPushState(url) {
        expect.step(url.split("?")[1]);
    }
    await createSwitchCompanyMenu({ onPushState });

    /**
     *   [x] **Company 1**
     *   [ ] Company 2
     *   [ ] Company 3
     */
    expect(getService("company").activeCompanyIds).toEqual([1]);
    expect(getService("company").currentCompany.id).toBe(1);
    expect("[data-company-id]").toHaveCount(3);
    expect("[data-company-id] .fa-check-square").toHaveCount(1);
    expect("[data-company-id] .fa-square-o").toHaveCount(2);

    /**
     *   [x] **Company 1**
     *   [x] Company 2      -> toggle
     *   [ ] Company 3
     */
    await toggle(1);
    expect("[data-company-id] .fa-check-square").toHaveCount(2);
    expect("[data-company-id] .fa-square-o").toHaveCount(1);
    await confirm();
    expect(["cids=1-2"]).toVerifySteps();
});

test("can toggle multiple companies at once", async () => {
    function onPushState(url) {
        expect.step(url.split("?")[1]);
    }
    await createSwitchCompanyMenu({ onPushState }, ORIGINAL_TOGGLE_DELAY);

    /**
     *   [x] **Company 1**
     *   [ ] Company 2
     *   [ ] Company 3
     */
    expect(getService("company").activeCompanyIds).toEqual([1]);
    expect(getService("company").currentCompany.id).toBe(1);
    expect("[data-company-id]").toHaveCount(3);
    expect("[data-company-id] .fa-check-square").toHaveCount(1);
    expect("[data-company-id] .fa-square-o").toHaveCount(2);

    /**
     *   [ ] **Company 1**  -> toggle all
     *   [x] Company 2      -> toggle all
     *   [x] Company 3      -> toggle all
     */
    await toggle(0);
    await toggle(1);
    await toggle(2);
    expect("[data-company-id] .fa-check-square").toHaveCount(2);
    expect("[data-company-id] .fa-square-o").toHaveCount(1);

    expect([]).toVerifySteps();
    await confirm();
    expect(["cids=2-3"]).toVerifySteps();
});

test("single company selected: toggling it off will keep it", async () => {
    await createSwitchCompanyMenu();

    /**
     *   [x] **Company 1**
     *   [ ] Company 2
     *   [ ] Company 3
     */
    await runAllTimers();
    expect(router.current).toEqual({ cids: 1 });
    expect(getService("company").activeCompanyIds).toEqual([1]);
    expect(getService("company").currentCompany.id).toBe(1);
    expect("[data-company-id]").toHaveCount(3);
    expect("[data-company-id] .fa-check-square").toHaveCount(1);
    expect("[data-company-id] .fa-square-o").toHaveCount(2);

    /**
     *   [ ] **Company 1**  -> toggle off
     *   [ ] Company 2
     *   [ ] Company 3
     */
    await toggle(0);
    await confirm();
    expect(router.current).toEqual({
        cids: 1,
    });
    expect(getService("company").activeCompanyIds).toEqual([1]);
    expect(getService("company").currentCompany.id).toBe(1);
    expect("[data-company-id] .fa-check-squarqe").toHaveCount(0);
    expect("[data-company-id] .fa-square-o").toHaveCount(3);
});

test("single company mode: companies can be logged in", async () => {
    function onPushState(url) {
        expect.step(url.split("?")[1]);
    }
    await createSwitchCompanyMenu({ onPushState });

    /**
     *   [x] **Company 1**
     *   [ ] Company 2
     *   [ ] Company 3
     */
    expect(getService("company").activeCompanyIds).toEqual([1]);
    expect(getService("company").currentCompany.id).toBe(1);
    expect("[data-company-id]").toHaveCount(3);
    expect("[data-company-id] .fa-check-square").toHaveCount(1);
    expect("[data-company-id] .fa-square-o").toHaveCount(2);

    /**
     *   [x] **Company 1**
     *   [ ] Company 2      -> log into
     *   [ ] Company 3
     */
    await contains(".log_into:eq(1)").click();
    expect(["cids=2"]).toVerifySteps();
});

test("multi company mode: log into a non selected company", async () => {
    function onPushState(url) {
        expect.step(url.split("?")[1]);
    }
    browser.location.search = "cids=3-1";
    await createSwitchCompanyMenu({ onPushState });

    /**
     *   [x] Company 1
     *   [ ] Company 2
     *   [x] **Company 3**
     */
    expect(getService("company").activeCompanyIds).toEqual([3, 1]);
    expect(getService("company").currentCompany.id).toBe(3);
    expect("[data-company-id]").toHaveCount(3);
    expect("[data-company-id] .fa-check-square").toHaveCount(2);
    expect("[data-company-id] .fa-square-o").toHaveCount(1);

    /**
     *   [x] Company 1
     *   [ ] Company 2      -> log into
     *   [x] **Company 3**
     */
    await contains(".log_into:eq(1)").click();
    expect(["cids=2"]).toVerifySteps();
});

test("multi company mode: log into an already selected company", async () => {
    function onPushState(url) {
        expect.step(url.split("?")[1]);
    }
    browser.location.search = "cids=2-3";
    await createSwitchCompanyMenu({ onPushState });

    /**
     *   [ ] Company 1
     *   [x] **Company 2**
     *   [x] Company 3
     */
    expect(getService("company").activeCompanyIds).toEqual([2, 3]);
    expect(getService("company").currentCompany.id).toBe(2);
    expect("[data-company-id]").toHaveCount(3);
    expect("[data-company-id] .fa-check-square").toHaveCount(2);
    expect("[data-company-id] .fa-square-o").toHaveCount(1);

    /**
     *   [ ] Company 1
     *   [x] **Company 2**
     *   [x] Company 3      -> log into
     */
    await contains(".log_into:eq(2)").click();
    expect(["cids=3"]).toVerifySteps();
});

test("companies can be logged in even if some toggled within delay", async () => {
    function onPushState(url) {
        expect.step(url.split("?")[1]);
    }
    await createSwitchCompanyMenu({ onPushState }, ORIGINAL_TOGGLE_DELAY);

    /**
     *   [x] **Company 1**
     *   [ ] Company 2
     *   [ ] Company 3
     */
    expect(getService("company").activeCompanyIds).toEqual([1]);
    expect(getService("company").currentCompany.id).toBe(1);
    expect("[data-company-id]").toHaveCount(3);
    expect("[data-company-id] .fa-check-square").toHaveCount(1);
    expect("[data-company-id] .fa-square-o").toHaveCount(2);

    /**
     *   [ ] **Company 1**  -> toggled
     *   [ ] Company 2      -> logged in
     *   [ ] Company 3      -> toggled
     */
    await contains("[data-company-id] [role=menuitemcheckbox]:eq(2)").click();
    await contains("[data-company-id] [role=menuitemcheckbox]:eq(0)").click();
    await contains(".log_into:eq(1)").click();
    expect(["cids=2"]).toVerifySteps();
});

test("show confirm and reset buttons only when selection has changed", async () => {
    await createSwitchCompanyMenu();
    expect(".o_switch_company_menu_buttons").toHaveCount(0);
    await toggle(1);
    expect(".o_switch_company_menu_buttons button").toHaveCount(2);
    await toggle(1);
    expect(".o_switch_company_menu_buttons").toHaveCount(0);
});

test("No collapse and no search input when less that 10 companies", async () => {
    await createSwitchCompanyMenu();
    expect(".o_burger_menu_companies .fa-caret-right").toHaveCount(0);
    expect(".o_burger_menu_companies .visually-hidden input").toHaveCount(1);
});

test("Show search input when more that 10 companies & search filters items but ignore case and spaces", async () => {
    patchWithCleanup(session.user_companies, {
        allowed_companies: {
            3: { id: 3, name: "Hermit", sequence: 1, parent_id: false, child_ids: [] },
            2: { id: 2, name: "Herman's", sequence: 2, parent_id: false, child_ids: [] },
            1: {
                id: 1,
                name: "Heroes TM",
                sequence: 3,
                parent_id: false,
                child_ids: [4, 5],
            },
            4: { id: 4, name: "Hercules", sequence: 4, parent_id: 1, child_ids: [] },
            5: { id: 5, name: "Hulk", sequence: 5, parent_id: 1, child_ids: [] },
            6: {
                id: 6,
                name: "Random Company a",
                sequence: 6,
                parent_id: false,
                child_ids: [7, 8],
            },
            7: {
                id: 7,
                name: "Random Company aa",
                sequence: 7,
                parent_id: 6,
                child_ids: [],
            },
            8: {
                id: 8,
                name: "Random Company ab",
                sequence: 8,
                parent_id: 6,
                child_ids: [],
            },
            9: { id: 9, name: "Random d", sequence: 9, parent_id: false, child_ids: [] },
            10: { id: 10, name: "Random e", sequence: 10, parent_id: false, child_ids: [] },
        },
        disallowed_ancestor_companies: {},
        current_company: 3,
    });
    await createSwitchCompanyMenu();
    await contains(".o_burger_menu_companies > div").click();
    expect(".o_burger_menu_companies input").toHaveCount(1);
    expect(".o_burger_menu_companies input").not.toBeFocused();

    expect(".o_switch_company_item").toHaveCount(10);
    contains(".o_burger_menu_companies input").edit("omcom");
    await animationFrame();

    expect(".o_switch_company_item").toHaveCount(3);
    expect(queryAllTexts(".o_switch_company_item.o-navigable")).toEqual([
        "Random Company a",
        "Random Company aa",
        "Random Company ab",
    ]);
});

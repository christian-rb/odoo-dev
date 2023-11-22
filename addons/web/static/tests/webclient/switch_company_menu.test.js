import { beforeEach, describe, expect, test } from "@odoo/hoot";
import { edit, keyDown, press, queryAll, queryAllAttributes, queryAllTexts } from "@odoo/hoot-dom";
import { animationFrame, runAllTimers } from "@odoo/hoot-mock";
import {
    contains,
    getService,
    mountWithCleanup,
    patchWithCleanup,
} from "@web/../tests/web_test_helpers";

import { browser } from "@web/core/browser/browser";
import { router } from "@web/core/browser/router";
import { session } from "@web/session";
import { SwitchCompanyMenu } from "@web/webclient/switch_company_menu/switch_company_menu";

const ORIGINAL_TOGGLE_DELAY = SwitchCompanyMenu.toggleDelay;

async function createSwitchCompanyMenu(routerParams = {}, toggleDelay = 0) {
    patchWithCleanup(SwitchCompanyMenu, { toggleDelay });
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
    await mountWithCleanup(SwitchCompanyMenu);
}

describe.current.tags("desktop");

async function open() {
    await contains(".dropdown-toggle").click();
}

async function toggle(index) {
    await contains(queryAll("[data-company-id] [role=menuitemcheckbox]")[index]).click();
}

async function confirm() {
    await contains(queryAll(".o_switch_company_menu_buttons button")[0]).click();
}

beforeEach(() => {
    patchWithCleanup(session.user_companies, {
        allowed_companies: {
            3: { id: 3, name: "Hermit", sequence: 1, parent_id: false, child_ids: [] },
            2: { id: 2, name: "Herman's", sequence: 2, parent_id: false, child_ids: [] },
            1: { id: 1, name: "Heroes TM", sequence: 3, parent_id: false, child_ids: [4, 5] },
            4: { id: 4, name: "Hercules", sequence: 4, parent_id: 1, child_ids: [] },
            5: { id: 5, name: "Hulk", sequence: 5, parent_id: 1, child_ids: [] },
        },
        disallowed_ancestor_companies: {},
        current_company: 3,
    });
});

test("basic rendering", async () => {
    await createSwitchCompanyMenu();

    expect("div.o_switch_company_menu").toHaveCount(1);
    expect("div.o_switch_company_menu").toHaveText("Hermit");

    await open();
    expect("[data-company-id] [role=menuitemcheckbox]").toHaveCount(5);
    expect(".log_into").toHaveCount(5);
    expect(".fa-check-square").toHaveCount(1);
    expect(".fa-square-o").toHaveCount(4);
    expect(".dropdown-item:has(.fa-check-square)").toHaveText("Hermit");
    expect(".dropdown-item:has(.fa-square-o):eq(0)").toHaveText("Herman's");
    expect(".dropdown-menu").toHaveText("Hermit\nHerman's\nHeroes TM\nHercules\nHulk");
});

test("companies can be toggled: toggle a second company", async () => {
    function onPushState(url) {
        expect.step(url.split("?")[1]);
    }
    await createSwitchCompanyMenu({ onPushState });

    /**
     *   [x] **Hermit**
     *   [ ] Herman's
     *   [ ] Heroes TM
     *   [ ]    Hercules
     *   [ ]    Hulk
     */
    expect(getService("company").activeCompanyIds).toEqual([3]);
    expect(getService("company").currentCompany.id).toBe(3);
    await open();
    expect("[data-company-id]").toHaveCount(5);
    expect("[data-company-id] .fa-check-square").toHaveCount(1);
    expect("[data-company-id] .fa-square-o").toHaveCount(4);
    expect(queryAllAttributes("[data-company-id] [role=menuitemcheckbox]", "aria-checked")).toEqual(
        ["true", "false", "false", "false", "false"]
    );
    expect(queryAllAttributes("[data-company-id] .log_into", "aria-pressed")).toEqual([
        "true",
        "false",
        "false",
        "false",
        "false",
    ]);

    /**
     *   [x] **Hermit**
     *   [x] Herman's      -> toggle
     *   [ ] Heroes TM
     *   [ ]    Hercules
     *   [ ]    Hulk
     */
    await toggle(1);
    expect(".dropdown-menu").toHaveCount(1, { message: "dropdown is still opened" });
    expect("[data-company-id] .fa-check-square").toHaveCount(2);
    expect("[data-company-id] .fa-square-o").toHaveCount(3);
    expect(queryAllAttributes("[data-company-id] [role=menuitemcheckbox]", "aria-checked")).toEqual(
        ["true", "true", "false", "false", "false"]
    );
    expect(queryAllAttributes("[data-company-id] .log_into", "aria-pressed")).toEqual([
        "true",
        "false",
        "false",
        "false",
        "false",
    ]);

    await confirm();
    expect(["cids=3-2"]).toVerifySteps();
});

test("can toggle multiple companies at once", async () => {
    function onPushState(url) {
        expect.step(url.split("?")[1]);
    }
    await createSwitchCompanyMenu({ onPushState }, ORIGINAL_TOGGLE_DELAY);

    /**
     *   [ ] Hermit          -> toggle all
     *   [x] **Herman's**    -> toggle all
     *   [x] Heroes TM       -> toggle all
     *   [ ]    Hercules
     *   [ ]    Hulk
     */
    expect(getService("company").activeCompanyIds).toEqual([3]);
    expect(getService("company").currentCompany.id).toBe(3);
    await open();
    expect("[data-company-id]").toHaveCount(5);
    expect("[data-company-id] .fa-check-square").toHaveCount(1);
    expect("[data-company-id] .fa-square-o").toHaveCount(4);

    /**
     *   [x] **Hermit**
     *   [x] Herman's      -> toggle
     *   [ ] Heroes TM
     *   [ ]    Hercules
     *   [ ]    Hulk
     */
    await toggle(0);
    await toggle(1);
    await toggle(2);
    expect(".dropdown-menu").toHaveCount(1, { message: "dropdown is still opened" });
    expect("[data-company-id] .fa-check-square").toHaveCount(4);
    expect("[data-company-id] .fa-square-o").toHaveCount(1);

    expect([]).toVerifySteps();
    await confirm();
    expect(["cids=2-1-4-5"]).toVerifySteps();
});

test("single company selected: toggling it off will keep it", async () => {
    await createSwitchCompanyMenu();

    /**
     *   [x] **Hermit**
     *   [ ] Herman's
     *   [ ] Heroes TM
     *   [ ]    Hercules
     *   [ ]    Hulk
     */
    await runAllTimers();
    expect(router.current).toEqual({ cids: 3 });
    expect(getService("company").activeCompanyIds).toEqual([3]);
    expect(getService("company").currentCompany.id).toBe(3);
    await open();
    expect("[data-company-id]").toHaveCount(5);
    expect("[data-company-id] .fa-check-square").toHaveCount(1);
    expect("[data-company-id] .fa-square-o").toHaveCount(4);

    /**
     *   [x] **Hermit**  -> toggle off
     *   [ ] Herman's
     *   [ ] Heroes TM
     *   [ ]    Hercules
     *   [ ]    Hulk
     */
    await toggle(0);
    await confirm();
    await animationFrame();
    expect(router.current).toEqual({
        cids: 3,
    });
    expect(getService("company").activeCompanyIds).toEqual([3]);
    expect(getService("company").currentCompany.id).toBe(3);

    await open();
    expect("[data-company-id] .fa-check-square").toHaveCount(0);
    expect("[data-company-id] .fa-square-o").toHaveCount(5);
});

test("single company mode: companies can be logged in", async () => {
    function onPushState(url) {
        expect.step(url.split("?")[1]);
    }
    await createSwitchCompanyMenu({ onPushState }, ORIGINAL_TOGGLE_DELAY);

    /**
     *   [x] **Hermit**
     *   [ ] Herman's
     *   [ ] Heroes TM
     *   [ ]    Hercules
     *   [ ]    Hulk
     */
    expect(getService("company").activeCompanyIds).toEqual([3]);
    expect(getService("company").currentCompany.id).toBe(3);
    await open();
    expect("[data-company-id]").toHaveCount(5);
    expect("[data-company-id] .fa-check-square").toHaveCount(1);
    expect("[data-company-id] .fa-square-o").toHaveCount(4);

    /**
     *   [ ] Hermit
     *   [x] **Herman's**     -> log into
     *   [ ] Heroes TM
     *   [ ]    Hercules
     *   [ ]    Hulk
     */
    await contains(".log_into:eq(1)").click();
    expect(".dropdown-menu").toHaveCount(0, { message: "dropdown is directly closed" });
    expect(["cids=2"]).toVerifySteps();
});

test("multi company mode: log into a non selected company", async () => {
    function onPushState(url) {
        expect.step(url.split("?")[1]);
    }
    browser.location.search = "cids=3-1";
    await createSwitchCompanyMenu({ onPushState });

    /**
     *   [x] Hermit
     *   [ ] Herman's
     *   [x] **Heroes TM**
     *   [ ]    Hercules
     *   [ ]    Hulk
     */
    expect(getService("company").activeCompanyIds).toEqual([3, 1]);
    expect(getService("company").currentCompany.id).toBe(3);
    await open();
    expect("[data-company-id]").toHaveCount(5);
    expect("[data-company-id] .fa-check-square").toHaveCount(2);
    expect("[data-company-id] .fa-square-o").toHaveCount(3);

    /**
     *   [ ] Hermit
     *   [x] **Herman's**    -> log into
     *   [ ] Heroes TM
     *   [ ]    Hercules
     *   [ ]    Hulk
     */
    await contains(".log_into:eq(1)").click();
    expect(".dropdown-menu").toHaveCount(0, { message: "dropdown is directly closed" });
    expect(["cids=2"]).toVerifySteps();
});

test("multi company mode: log into an already selected company", async () => {
    function onPushState(url) {
        expect.step(url.split("?")[1]);
    }
    browser.location.search = "cids=2-1";
    await createSwitchCompanyMenu({ onPushState });

    /**
     *   [ ] Hermit
     *   [x] **Herman's**
     *   [x] Heroes TM
     *   [ ]    Hercules
     *   [ ]    Hulk
     */
    expect(getService("company").activeCompanyIds).toEqual([2, 1]);
    expect(getService("company").currentCompany.id).toBe(2);
    await open();
    expect("[data-company-id]").toHaveCount(5);
    expect("[data-company-id] .fa-check-square").toHaveCount(2);
    expect("[data-company-id] .fa-square-o").toHaveCount(3);

    /**
     *   [ ] Hermit
     *   [ ] Herman's
     *   [x] **Heroes TM**    -> log into
     *   [x]    Hercules
     *   [x]    Hulk
     */
    await contains(".log_into:eq(2)").click();
    expect(".dropdown-menu").toHaveCount(0, { message: "dropdown is directly closed" });
    expect(["cids=1-4-5"]).toVerifySteps();
});

test("companies can be logged in even if some toggled within delay", async () => {
    function onPushState(url) {
        expect.step(url.split("?")[1]);
    }
    await createSwitchCompanyMenu({ onPushState }, ORIGINAL_TOGGLE_DELAY);

    /**
     *   [x] **Hermit**
     *   [ ] Herman's
     *   [ ] Heroes TM
     *   [ ]    Hercules
     *   [ ]    Hulk
     */
    expect(getService("company").activeCompanyIds).toEqual([3]);
    expect(getService("company").currentCompany.id).toBe(3);
    await open();
    expect("[data-company-id]").toHaveCount(5);
    expect("[data-company-id] .fa-check-square").toHaveCount(1);
    expect("[data-company-id] .fa-square-o").toHaveCount(4);

    /**
     *   [ ] Hermit         -> toggled
     *   [x] **Herman's**   -> logged in
     *   [ ] Heroes TM      -> toggled
     *   [ ]    Hercules
     *   [ ]    Hulk
     */
    await contains("[data-company-id] [role=menuitemcheckbox]:eq(2)").click();
    await contains("[data-company-id] [role=menuitemcheckbox]:eq(0)").click();
    await contains(".log_into:eq(1)").click();
    expect(".dropdown-menu").toHaveCount(0, { message: "dropdown is directly closed" });
    expect(["cids=2"]).toVerifySteps();
});

test.tags("desktop")("show confirm and reset buttons only when selection has changed", async () => {
    await createSwitchCompanyMenu();
    await open();

    expect(".o_switch_company_menu_buttons").toHaveCount(0);

    await toggle(1);
    expect(".o_switch_company_menu_buttons button").toHaveCount(2);

    await toggle(1);
    expect(".o_switch_company_menu_buttons").toHaveCount(0);
});

test.tags("desktop")("No search input when less that 10 companies", async () => {
    await createSwitchCompanyMenu();

    await open();
    expect(".o-dropdown--menu .visually-hidden input").toHaveCount(1);
});

test.tags("desktop")(
    "Show search input when more that 10 companies & search filters items but ignore case and spaces",
    async () => {
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

        await open();
        expect(".o-dropdown--menu input").toHaveCount(1);
        expect(".o-dropdown--menu input").toBeFocused();
        expect(".o-dropdown--menu .o_switch_company_item").toHaveCount(10);

        edit("omcom");
        await animationFrame();
        expect(".o-dropdown--menu .o_switch_company_item").toHaveCount(3);

        expect(queryAllTexts(".o-dropdown--menu .o_switch_company_item")).toEqual([
            "Random Company a",
            "Random Company aa",
            "Random Company ab",
        ]);
    }
);

test.tags("desktop")(
    "When less than 10 companies, typing key makes the search field appear",
    async () => {
        await createSwitchCompanyMenu();
        await open();

        expect(".o-dropdown--menu input").toHaveCount(1);
        expect(".o-dropdown--menu input").toBeFocused();
        expect(".o-dropdown--menu .visually-hidden input").toHaveCount(1);

        edit("a");
        await animationFrame();

        expect(".o-dropdown--menu input").toHaveValue("a");
        expect(".o-dropdown--menu :not(.visually-hidden) input").toHaveCount(1);
    }
);

test.tags("desktop")("Navigation with search input", async () => {
    patchWithCleanup(session.user_companies, {
        allowed_companies: {
            3: { id: 3, name: "Hermit", sequence: 1, parent_id: false, child_ids: [] },
            2: { id: 2, name: "Herman's", sequence: 2, parent_id: false, child_ids: [] },
            1: { id: 1, name: "Heroes TM", sequence: 3, parent_id: false, child_ids: [4, 5] },
            4: { id: 4, name: "Hercules", sequence: 4, parent_id: 1, child_ids: [] },
            5: { id: 5, name: "Hulk", sequence: 5, parent_id: 1, child_ids: [] },
            6: {
                id: 6,
                name: "Random Company a",
                sequence: 6,
                parent_id: false,
                child_ids: [7, 8],
            },
            7: { id: 7, name: "Random Company aa", sequence: 7, parent_id: 6, child_ids: [] },
            8: { id: 8, name: "Random Company ab", sequence: 8, parent_id: 6, child_ids: [] },
            9: { id: 9, name: "Random d", sequence: 9, parent_id: false, child_ids: [] },
            10: { id: 10, name: "Random e", sequence: 10, parent_id: false, child_ids: [] },
        },
        disallowed_ancestor_companies: {},
        current_company: 3,
    });

    await createSwitchCompanyMenu({ onPushState: (url) => expect.step(url.split("?")[1]) });
    await open();

    expect(".o-dropdown--menu input").toBeFocused();
    expect(".o_switch_company_item.focus").toHaveCount(0);

    const navigationEvents = [
        { hotkey: "arrowdown", focused: 1, selectedCompanies: [3] }, // Go to first item
        { hotkey: "arrowup", focused: 0 }, // Go to search input
        { hotkey: "arrowup", focused: 10 }, // Go to last item
        { hotkey: "Space", focused: 10, selectedCompanies: [3, 10] }, // Select last item
        { hotkey: "shift+tab", focused: 9, selectedCompanies: [3, 10] }, // Go to previous item
        { hotkey: "tab", focused: 10, selectedCompanies: [3, 10] }, // Go to next item
        { hotkey: "Space", focused: 10, selectedCompanies: [3] }, // Deselect last item
        { hotkey: "arrowdown", focused: 0 }, // Go to seach input
        { input: "a", focused: 0 }, // Type "a"
        { hotkey: "arrowdown", focused: 1 }, // Go to first item
        { hotkey: "Space", focused: 1, selectedCompanies: [2] }, // Select first item
    ];

    for (let i = 0; i < navigationEvents.length; i++) {
        const { hotkey, focused, selectedCompanies, input } = navigationEvents[i];
        if (hotkey) {
            press(hotkey);
        }

        if (input) {
            edit(input);
        }

        // Ensure debounced mutation listener update and owl re-render
        await animationFrame();
        await runAllTimers();

        const item = queryAll(".o_popover .o-navigable")[focused];
        expect(item).toHaveClass("focus", {
            message: `step ${i}: item has focus class (${JSON.stringify(navigationEvents[i])})`,
        });
        expect(item).toBeFocused({
            message: `step ${i}: item is focused (${JSON.stringify(navigationEvents[i])})`,
        });

        if (selectedCompanies) {
            const companies = queryAllAttributes(
                ".o_switch_company_item:has([role=menuitemcheckbox][aria-checked=true])",
                "data-company-id"
            ).map((i) => parseInt(i));

            expect(companies).toEqual(selectedCompanies, {
                message: `step ${i}: selected companies match`,
            });
        }
    }

    keyDown("control+enter");
    await animationFrame();

    expect(["cids=3-2"]).toVerifySteps();
    expect(".o_switch_company_item").toHaveCount(0);
});

test.tags("desktop")("Select and de-select all", async () => {
    await createSwitchCompanyMenu();
    await open();

    // Show search
    edit(" ");
    await animationFrame();

    // One company is selected, there should be a check box with minus inside
    expect("[role=menuitemcheckbox][title='Deselect all'] i").toHaveClass("fa-minus-square-o");

    await contains("[role=menuitemcheckbox][title='Deselect all']").click();
    // No company is selected, there should be a empty check box
    expect("[role=menuitemcheckbox][title='Select all'] i").toHaveClass("fa-square-o");
    expect(".o_switch_company_item:has([role=menuitemcheckbox][aria-checked=true])").toHaveCount(0);

    await contains("[role=menuitemcheckbox][title='Select all']").click();
    // All companies are selected, there should be a checked check box
    expect("[role=menuitemcheckbox][title='Deselect all'] i").toHaveClass("fa-check-square");
    expect(".o_switch_company_item:has([role=menuitemcheckbox][aria-checked=true])").toHaveCount(5);

    await contains("[role=menuitemcheckbox][title='Deselect all']").click();
    // No company is selected, there should be a empty check box
    expect("[role=menuitemcheckbox][title='Select all'] i").toHaveClass("fa-square-o");
    expect(".o_switch_company_item:has([role=menuitemcheckbox][aria-checked=true])").toHaveCount(0);
});

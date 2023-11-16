import { expect, test } from "@odoo/hoot";
import { click, edit, keyDown, keyUp, queryAllTexts, queryOne } from "@odoo/hoot-dom";
import { animationFrame, runAllTimers } from "@odoo/hoot-mock";
import {
    contains,
    defineWebModels,
    mountWithCleanup,
    serverState,
} from "@web/../tests/web_test_helpers";
import { WebClient } from "@web/webclient/webclient";
import { browser } from "@web/core/browser/browser";

async function _checkSteps(steps) {
    click(".o_button_steps");
    await animationFrame();
    expect(queryAllTexts(".o_tour_step")).toEqual(steps);
    click(".o_button_steps");
    await animationFrame();
}

test("Click on element with unique odoo class", async () => {
    await mountWithCleanup(`
        <div class="o_parent">
            <div class="o_child_1 click"></div>
            <div class="o_child_2"></div>
            <div class="o_child_3"></div>
        </div>
    `);

    expect(".o_tour_recorder").toHaveCount(1);
    click(".o_button_record");
    await animationFrame();
    click(".click");
    await animationFrame();
    await _checkSteps(["1. .o_child_1"]);

    click(".o_child_2");
    await animationFrame();
    await _checkSteps(["1. .o_child_1", "2. .o_child_2"]);
});

test("Click on element with no unique odoo class", async () => {
    await mountWithCleanup(`
        <div class="o_parent">
            <div class="o_child_1 click"></div>
            <div class="o_child_1"></div>
            <div class="o_child_1"></div>
        </div>
    `);

    expect(".o_tour_recorder").toHaveCount(1);
    click(".o_button_record");
    await animationFrame();
    click(".click");
    await animationFrame();
    await _checkSteps(["1. .o_child_1:nth-child(1)"]);
});

test("Click on elements with no odoo class", async () => {
    await mountWithCleanup(`
        <div>
            <div></div>
            <div class="click"></div>
            <div></div>
        </div>
    `);

    expect(".o_tour_recorder").toHaveCount(1);
    click(".o_button_record");
    await animationFrame();
    click(".click");
    await animationFrame();
    await _checkSteps([
        "1. div:nth-child(1) > div:nth-child(2)", // There is a "nth-child" on the first div because of the div "o-main-components-container"
    ]);
});

test("Click on elements with 'data-menu-xmlid' attribute", async () => {
    await mountWithCleanup(`
        <div>
            <div></div>
            <div data-menu-xmlid="my_menu_1" class="click_1"></div>
            <div data-menu-xmlid="my_menu_2" class="click_2 o_div"></div>
            <div></div>
        </div>
    `);

    expect(".o_tour_recorder").toHaveCount(1);
    click(".o_button_record");
    await animationFrame();
    click(".click_1");
    click(".click_2");
    await animationFrame();
    await _checkSteps([
        "1. div[data-menu-xmlid='my_menu_1']",
        "2. .o_div[data-menu-xmlid='my_menu_2']",
    ]);
});

test("Click on elements with 'name' attribute", async () => {
    await mountWithCleanup(`
        <div>
            <div></div>
            <div name="sale_id" class="click_1"></div>
            <div name="partner_id" class="click_2 o_div"></div>
            <div></div>
        </div>
    `);

    expect(".o_tour_recorder").toHaveCount(1);
    click(".o_button_record");
    await animationFrame();
    click(".click_1");
    click(".click_2");
    await animationFrame();
    await _checkSteps(["1. div[name='sale_id']", "2. .o_div[name='partner_id']"]);
});

test("Click on element that have a link or button has parent", async () => {
    await mountWithCleanup(`
        <div>
            <button class="o_button"><i class="click_1">icon</i></button>
            <a class="o_link"><span class="click_2">This is my link</span></a>
        </div>
    `);

    expect(".o_tour_recorder").toHaveCount(1);
    click(".o_button_record");
    await animationFrame();
    click(".click_1");
    click(".click_2");
    await animationFrame();
    await _checkSteps(["1. .o_button", "2. .o_link"]);
});

test("Click on element with path that can be reduced", async () => {
    await mountWithCleanup(`
        <div class=".o_parent">
            <div name="field_name">
                <div class="o_div_2">
                    <div class="o_div_3 click"></div>
                </div>
            </div>
            <div name="field_partner_id">
                <div class="o_div_2">
                    <div class="o_div_3"></div>
                </div>
            </div>
        </div>
    `);

    expect(".o_tour_recorder").toHaveCount(1);
    click(".o_button_record");
    await animationFrame();
    click(".click");
    await animationFrame();
    await _checkSteps(["1. div[name='field_name'] .o_div_3"]);
});

test("Click on input", async () => {
    await mountWithCleanup(`
        <div class=".o_parent">
            <input type="text" class="click"/>
        </div>
    `);

    expect(".o_tour_recorder").toHaveCount(1);
    click(".o_button_record");
    await animationFrame();
    click(".click");
    await animationFrame();
    expect(".o_button_record").toHaveText("Record (recording keyboard)");
    await _checkSteps(["1. input"]);
});

test("Click on tag that is inside a contenteditable", async () => {
    await mountWithCleanup(`
        <div class=".o_parent">
            <div class="o_editor" contenteditable="true">
                <p class="click oe-hint oe-command-temporary-hint" placeholder="My placeholder..."></p>
            </div>
        </div>
    `);

    expect(".o_tour_recorder").toHaveCount(1);
    click(".o_button_record");
    await animationFrame();
    click(".click");
    await animationFrame();
    expect(".o_button_record").toHaveText("Record (recording keyboard)");
    await _checkSteps(["1. .o_editor[contenteditable='true']"]);
});

test("Remove step during recording", async () => {
    await mountWithCleanup(`
        <div class="o_parent">
            <div class="o_child click"></div>
        </div>
    `);

    expect(".o_tour_recorder").toHaveCount(1);
    click(".o_button_record");
    await animationFrame();
    click(".click");
    await animationFrame();
    await _checkSteps(["1. .o_child"]);
    click(".o_button_steps");
    await animationFrame();
    contains(".o_button_delete_step").click();
    click(".o_button_steps");
    await animationFrame();
    await _checkSteps([]);
});

test("Edit input", async () => {
    await mountWithCleanup(`
        <div class="o_parent">
            <input type="text" class="click"/>
        </div>
    `);

    expect(".o_tour_recorder").toHaveCount(1);
    click(".o_button_record");
    await animationFrame();
    click(".click");
    await animationFrame();
    expect(".o_button_record").toHaveText("Record (recording keyboard)");
    edit("Bismillah");
    await _checkSteps(["1. input\n(run: edit Bismillah)"]);
});

test("Save a custom tour in the localStorage", async () => {
    await mountWithCleanup(`
        <div class="o_parent">
            <div class="click"></div>
        </div>
    `);

    expect(".o_tour_recorder").toHaveCount(1);
    click(".o_button_record");
    await animationFrame();
    click(".click");
    await animationFrame();
    await _checkSteps(["1. .o_parent > div"]);

    click(".o_button_save");
    await animationFrame();
    await contains("input[name='name']").click();
    edit("tour_name");
    await animationFrame();
    click(".o_button_save_confirm");
    await animationFrame();

    const customToursString = browser.localStorage.getItem("custom_tours");
    const customTours = JSON.parse(customToursString);
    expect(customTours).toEqual([
        {
            name: "tour_name",
            url: "/odoo?cids=1",
            test: true,
            steps: [
                {
                    trigger: ".o_parent > div",
                },
            ],
        },
    ]);
});

test("Save a custom tour and check the tour dialog", async () => {
    serverState.debug = 1;

    defineWebModels();
    await mountWithCleanup(WebClient);

    await mountWithCleanup(
        `
        <div class="o_parent">
            <div class="click"></div>
        </div>
    `,
        { noMainContainer: true }
    );

    expect(".o_tour_recorder").toHaveCount(1);
    click(".o_button_record");
    await animationFrame();
    click(".click");
    await animationFrame();
    await _checkSteps(["1. .o_parent > div"]);

    click(".o_button_save");
    await animationFrame();
    await contains("input[name='name']").click();
    edit("tour_name");
    await animationFrame();
    click(".o_button_save_confirm");
    await animationFrame();
    expect(".o_notification_manager .o_notification_body").toHaveText(
        "Custom Tour 'tour_name' has been saved."
    );

    click(".o_debug_manager > button");
    await contains(".o-dropdown-item:contains('Start Tour')").click();

    expect("table tr td:contains('tour_name')").toHaveCount(1);
});

test("Delete saved custom tour and check the tour dialog", async () => {
    serverState.debug = 1;

    defineWebModels();
    await mountWithCleanup(WebClient);

    await mountWithCleanup(
        `
        <div class="o_parent">
            <div class="click"></div>
        </div>
    `,
        { noMainContainer: true }
    );

    expect(".o_tour_recorder").toHaveCount(1);
    click(".o_button_record");
    await animationFrame();
    click(".click");
    await animationFrame();
    await _checkSteps(["1. .o_parent > div"]);

    click(".o_button_save");
    await animationFrame();
    await contains("input[name='name']").click();
    edit("tour_name");
    await animationFrame();
    click(".o_button_save_confirm");
    await runAllTimers(); // Wait that the save notification disappear

    click(".o_debug_manager > button");
    await contains(".o-dropdown-item:contains('Start Tour')").click();

    expect("table tr td:contains('tour_name')").toHaveCount(1);

    click(".o_button_extra");
    await contains(".o-dropdown-item:contains('Delete')").click();

    expect(".o_notification_manager .o_notification_body").toHaveText(
        "Tour 'tour_name' correctly deleted."
    );
    expect("table tr td:contains('tour_name')").toHaveCount(0);

    const customToursString = browser.localStorage.getItem("custom_tours");
    const customTours = JSON.parse(customToursString);
    expect(customTours).toEqual([]);
});

test("Drag and drop", async () => {
    await mountWithCleanup(`
        <div class="o_parent">
            <div>
                <div class="o_drag">drag me</div>
            </div>
            <div class="o_drop"></div>
        </div>
    `);

    expect(".o_tour_recorder").toHaveCount(1);
    click(".o_button_record");
    await animationFrame();
    await contains(".o_drag").dragAndDrop(".o_drop");
    await animationFrame();
    await _checkSteps(["1. .o_drag\n(run: drag_and_drop_native .o_drop)"]);
});

test("Edit contenteditable", async () => {
    await mountWithCleanup(`
        <div class="o_parent">
            <div class="o_editor click" contenteditable="true" style="width: 50px; height: 50px">
            </div>
        </div>
    `);

    expect(".o_tour_recorder").toHaveCount(1);
    click(".o_button_record");
    await animationFrame();
    click(".click");
    await animationFrame();
    expect(".o_editor").toBeFocused();
    expect(".o_button_record").toHaveText("Record (recording keyboard)");
    keyDown("B");
    await animationFrame();
    queryOne(".o_editor").appendChild(document.createTextNode("Bismillah"));
    keyUp("B");
    await animationFrame();
    await _checkSteps(["1. .o_editor[contenteditable='true']\n(run: editor Bismillah)"]);
});

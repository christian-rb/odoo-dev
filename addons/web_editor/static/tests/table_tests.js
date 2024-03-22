import { setSelection, nodeSize } from "@web_editor/js/editor/odoo-editor/src/utils/utils";
import { makeView, setupViewRegistries } from "@web/../tests/views/helpers";
import { patchWithCleanup, nextTick } from "@web/../tests/helpers/utils";
import { Wysiwyg } from "@web_editor/js/wysiwyg/wysiwyg";
import { triggerEvent, unformat, insertText } from "@web_editor/js/editor/odoo-editor/test/utils";

function onMount() {
    const editor = wysiwyg.odooEditor;
    const editable = editor.editable;
    editor.testMode = true;
    return { editor, editable };
}

let serverData;
let wysiwyg;

QUnit.module(
    "Table",
    {
        before: function () {
            serverData = {
                models: {
                    note: {
                        fields: {
                            body: {
                                string: "Editor",
                                type: "html",
                            },
                        },
                        records: [
                            {
                                id: 1,
                                display_name: "first record",
                                body: unformat(`
                                        <table class='table table-bordered o_table'><tbody>
                                            <tr><td><br></td><td><br></td><td><br></td></tr>
                                            <tr><td><br></td><td><br></td><td><br></td></tr>
                                        </tbody></table>`),
                            },
                        ],
                    },
                },
            };
        },
        beforeEach: async function () {
            setupViewRegistries();
            patchWithCleanup(Wysiwyg.prototype, {
                init() {
                    super.init(...arguments);
                    wysiwyg = this;
                },
            });
            await makeView({
                type: "form",
                serverData,
                resModel: "note",
                arch:
                    "<form>" +
                    '<field name="body" widget="html" style="height: 100px"/>' +
                    "</form>",
                resId: 1,
            });
        },
    },
    function () {
        QUnit.module("Table selection");

        QUnit.test("Select cells symmetrically using keyboard", async function (assert) {
            const { editor, editable } = onMount();
            const firstTd = editable.querySelector("td");
            setSelection(firstTd, 0);
            triggerEvent(editor.editable, "keydown", { key: "ArrowRight", shiftKey: true });
            await nextTick();
            assert.strictEqual(
                editable.innerHTML,
                unformat(`
                    <table class="table table-bordered o_table o_selected_table"><tbody>
                        <tr><td class="o_selected_td"><br></td><td><br></td><td><br></td></tr>
                        <tr><td><br></td><td><br></td><td><br></td></tr>
                    </tbody></table>`, "Should select single empty cell"),
            )
            triggerEvent(editor.editable, "keydown", { key: "ArrowRight", shiftKey: true });
            await nextTick();
            assert.strictEqual(
                editable.innerHTML,
                unformat(`
                    <table class="table table-bordered o_table o_selected_table"><tbody>
                        <tr><td class="o_selected_td"><br></td><td class="o_selected_td"><br></td><td><br></td></tr>
                        <tr><td><br></td><td><br></td><td><br></td></tr>
                    </tbody></table>`, "Should select two cells consecutively"),
            )
            triggerEvent(editor.editable, "keydown", { key: "ArrowDown", shiftKey: true });
            await nextTick();
            assert.strictEqual(
                editable.innerHTML,
                unformat(`
                    <table class="table table-bordered o_table o_selected_table"><tbody>
                        <tr><td class="o_selected_td"><br></td><td class="o_selected_td"><br></td><td><br></td></tr>
                        <tr><td class="o_selected_td"><br></td><td class="o_selected_td"><br></td><td><br></td></tr>
                    </tbody></table>`, "Should select four cells consecutively"),
            )
            triggerEvent(editor.editable, "keydown", { key: "ArrowRight", shiftKey: true });
            await nextTick();
            assert.strictEqual(
                editable.innerHTML,
                unformat(`
                    <table class="table table-bordered o_table o_selected_table"><tbody>
                        <tr><td class="o_selected_td"><br></td><td class="o_selected_td"><br></td><td class="o_selected_td"><br></td></tr>
                        <tr><td class="o_selected_td"><br></td><td class="o_selected_td"><br></td><td class="o_selected_td"><br></td></tr>
                    </tbody></table>`, "Should select six cells consecutively"),
            )
        });
        QUnit.test("Select single cell containing text", async function (assert) {
            const { editor, editable } = onMount();
            const firstTd = editable.querySelector("td");
            setSelection(firstTd, 0);
            insertText(editor, 'ab');
            setSelection(firstTd, 0, firstTd, nodeSize(firstTd));
            triggerEvent(editor.editable, "keydown", { key: "ArrowRight", shiftKey: true });
            await nextTick();
            assert.strictEqual(
                editable.innerHTML,
                unformat(`
                    <table class="table table-bordered o_table o_selected_table"><tbody>
                        <tr><td class="o_selected_td">ab</td><td><br></td><td><br></td></tr>
                        <tr><td><br></td><td><br></td><td><br></td></tr>
                    </tbody></table>`, "Should select single cell containing text"),
            )
        });
    }
);

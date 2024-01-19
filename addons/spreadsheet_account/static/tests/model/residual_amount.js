import { setCellContent } from "@spreadsheet/../tests/utils/commands";
import { createModelWithDataSource } from "@spreadsheet/../tests/utils/model";
import { waitForDataLoaded } from "@spreadsheet/helpers/model";
import { getEvaluatedCell } from "@spreadsheet/../tests/utils/getters";
import "@spreadsheet_account/index";

QUnit.module("spreadsheet_account > residual amount", {}, () => {
    QUnit.test("Basic evaluation", async (assert) => {
        const model = await createModelWithDataSource({
            mockRPC: async function (route, args) {
                if (args.method === "get_residual_amount") {
                    assert.step("get_residual_amount");
                    assert.deepEqual(args.args, [
                        [
                            {
                                codes: [
                                    "112",
                                ],
                                date_range: {
                                    range_type: "year",
                                    year: 2023,
                                },
                                company_id: 0,
                                include_unposted: false,
                            }
                        ],
                    ]);
                    return [111.11];
                }
            },
        });
        setCellContent(model, "A1", `=ODOO.RESIDUAL("112", 2023)`);
        await waitForDataLoaded(model);
        assert.verifySteps(["get_residual_amount"]);
        assert.strictEqual(getEvaluatedCell(model, "A1").value, 111.11);
    });

    QUnit.test("with wrong date format", async (assert) => {
        const model = await createModelWithDataSource();
        setCellContent(model, "A1", `=ODOO.RESIDUAL("112", "This is not a valid date")`);
        assert.equal(
            getEvaluatedCell(model, "A1").message,
            "'This is not a valid date' is not a valid period. Supported formats are \"21/12/2022\", \"Q1/2022\", \"12/2022\", and \"2022\"."
        );
    });

    QUnit.test("with no date", async (assert) => {
        const d = new Date();
        const model = await createModelWithDataSource({
            mockRPC: async function (route, args) {
                if (args.method === "get_residual_amount") {
                    assert.step("get_residual_amount");
                    assert.deepEqual(args.args, [
                        [
                            {
                                codes: [
                                    "112",
                                ],
                                date_range: {
                                    range_type: "year",
                                    year: d.getFullYear(),
                                },
                                company_id: 0,
                                include_unposted: false,
                            }
                        ],
                    ]);
                    return [111.11];
                }
            },
        });
        setCellContent(model, "A1", `=ODOO.RESIDUAL("112")`);
        await waitForDataLoaded(model);
        assert.verifySteps(["get_residual_amount"]);
        assert.strictEqual(getEvaluatedCell(model, "A1").value, 111.11);
    });
});

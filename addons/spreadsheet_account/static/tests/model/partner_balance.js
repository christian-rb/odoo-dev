import { setCellContent } from "@spreadsheet/../tests/utils/commands";
import { createModelWithDataSource } from "@spreadsheet/../tests/utils/model";
import { roundPrecision } from "@web/core/utils/numbers";
import { waitForDataLoaded } from "@spreadsheet/helpers/model";
import { getEvaluatedCell } from "@spreadsheet/../tests/utils/getters";
import "@spreadsheet_account/index";

QUnit.module("spreadsheet_account > partner balance", {}, () => {
    QUnit.test("Basic evaluation", async (assert) => {
        const model = await createModelWithDataSource({
            mockRPC: async function (route, args) {
                if (args.method === "spreadsheet_fetch_debit_credit") {
                    assert.step("spreadsheet_fetch_debit_credit");
                    assert.deepEqual(args.args, [
                        [
                            {
                                partner_ids: [
                                    14, 16
                                ],
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
                    return [{debit: 42, credit: 16}];
                }
            },
        });
        setCellContent(model, "A1", `=ODOO.PARTNER.BALANCE("14, 16", "112", 2023)`);
        await waitForDataLoaded(model);
        assert.verifySteps(["spreadsheet_fetch_debit_credit"]);
        assert.strictEqual(roundPrecision(getEvaluatedCell(model, "A1").value, 2), 26);
    });

    QUnit.test("with wrong date format", async (assert) => {
        const model = await createModelWithDataSource();
        setCellContent(model, "A1", `=ODOO.PARTNER.BALANCE("14, 16", "112", "This is not a valid date")`);
        assert.equal(
            getEvaluatedCell(model, "A1").message,
            "'This is not a valid date' is not a valid period. Supported formats are \"21/12/2022\", \"Q1/2022\", \"12/2022\", and \"2022\"."
        );
    });

    QUnit.test("with no date", async (assert) => {
        const d = new Date();
        const model = await createModelWithDataSource({
            mockRPC: async function (route, args) {
                if (args.method === "spreadsheet_fetch_debit_credit") {
                    assert.step("spreadsheet_fetch_debit_credit");
                    assert.deepEqual(args.args, [
                        [
                            {
                                partner_ids: [
                                    14, 16
                                ],
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
                    return [{debit: 42, credit: 16}];
                }
            },
        });
        setCellContent(model, "A1", `=ODOO.PARTNER.BALANCE("14, 16", "112")`);
        await waitForDataLoaded(model);
        assert.verifySteps(["spreadsheet_fetch_debit_credit"]);
        assert.strictEqual(roundPrecision(getEvaluatedCell(model, "A1").value, 2), 26);
    });
});

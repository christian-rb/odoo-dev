import { patch } from "@web/core/utils/patch";

import { accountTaxHelpers } from "@account/helpers/account_tax";

// ----------------------------------------F---------------------------------
// HELPERS IN BOTH PYTHON/JAVASCRIPT (account_tax.js / account_tax.py)
// -------------------------------------------------------------------------

patch(accountTaxHelpers, {
    /** override **/
    ascending_process_fixed_taxes_batch(batch) {
        super.ascending_process_fixed_taxes_batch(...arguments);

        if (batch.amount_type === "code") {
            batch.is_tax_computed = true;
        }
    },

    /** override **/
    descending_process_price_included_taxes_batch(batch) {
        super.descending_process_price_included_taxes_batch(...arguments);

        if (batch.price_include && batch.amount_type === "code") {
            batch.is_base_computed = true;
        }
    },

    /** override **/
    ascending_process_taxes_batch(batch) {
        super.ascending_process_taxes_batch(...arguments);

        if (!batch.price_include && batch.amount_type === "code") {
            batch.is_base_computed = true;
        }
    },

    /**
     * [!] Mirror of the same method in account_tax.py.
     * PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.
     */
    eval_tax_amount_formula(tax_values, evaluation_context) {
        const raw_base =
            evaluation_context.quantity * evaluation_context.price_unit +
            evaluation_context.extra_base;
        const formula_context = {
            price_unit: evaluation_context.price_unit,
            quantity: evaluation_context.quantity,
            product: evaluation_context.product,
            base: raw_base,
            min: Math.min,
            max: Math.max,
        };

        // Don't use 'eval' because we want a scoped context for the evaluation.
        // We can't use the 'with(scope){...}' syntax because it's not allowed in strict mode.
        const restricted_eval = Function.apply(null, [
            ...Object.keys(formula_context),
            "expr",
            `"use strict"; return ${tax_values._js_formula}`,
        ]);
        return restricted_eval.apply(null, [...Object.values(formula_context)]);
    },

    /** override **/
    eval_tax_amount(tax_values, evaluation_context) {
        if (tax_values.amount_type === "code") {
            return this.eval_tax_amount_formula(tax_values, evaluation_context);
        }
        return super.eval_tax_amount(...arguments);
    },
});

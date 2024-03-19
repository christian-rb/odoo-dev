import { roundPrecision } from "@web/core/utils/numbers";

export const accountTaxHelpers = {
    // -------------------------------------------------------------------------
    // HELPERS IN BOTH PYTHON/JAVASCRIPT (account_tax.js / account_tax.py)

    // PREPARE TAXES COMPUTATION
    // -------------------------------------------------------------------------

    /**
     * [!] Mirror of the same method in account_tax.py.
     * PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.
     */
    prepare_taxes_batches(taxes_data, { special_mode = false } = {}) {
        // Flatten the taxes and order them.
        const sorted_taxes_data = taxes_data.sort(
            (v1, v2) => v1.sequence - v2.sequence || v1.id - v2.id
        );
        let flatten_taxes_data = [];
        for (const tax_data of sorted_taxes_data) {
            if (tax_data.amount_type === "group") {
                const sorted_children_tax_ids = tax_data._children_tax_ids.sort(
                    (v1, v2) => v1.sequence - v2.sequence || v1.id - v2.id
                );
                for (const child_tax_data of sorted_children_tax_ids) {
                    flatten_taxes_data.push(child_tax_data);
                }
            } else {
                flatten_taxes_data.push(tax_data);
            }
        }
        flatten_taxes_data = flatten_taxes_data.map((tax_data, index) =>
            Object.assign(
                {},
                tax_data,
                {
                    price_include: special_mode === "total_included" ? true : tax_data.price_include,
                    _original_price_include: tax_data.price_include,
                    index: index,
                    evaluation_context: { special_mode: special_mode },
                }
            )
        );

        const batches = [];

        let current_batch = null;
        let is_base_affected = null;
        for (const tax_data of flatten_taxes_data.toReversed()) {
            if (current_batch !== null) {
                const same_amount_type = tax_data.amount_type === current_batch.amount_type;
                const same_price_include = tax_data.price_include === current_batch.price_include;
                const same_incl_base_amount_not_affected =
                    tax_data.include_base_amount &&
                    tax_data.include_base_amount === current_batch.include_base_amount &&
                    !is_base_affected;
                const same_inc_base_amount =
                    tax_data.include_base_amount === current_batch.include_base_amount &&
                    !tax_data.include_base_amount;
                const same_batch =
                    same_amount_type &&
                    same_price_include &&
                    (same_inc_base_amount || same_incl_base_amount_not_affected);
                if (!same_batch) {
                    batches.push(current_batch);
                    current_batch = null;
                }
            }

            if (current_batch === null) {
                current_batch = {
                    taxes: [],
                    amount_type: tax_data.amount_type,
                    include_base_amount: tax_data.include_base_amount,
                    price_include: tax_data.price_include,
                    is_tax_computed: false,
                    is_base_computed: false,
                };
            }

            is_base_affected = tax_data.is_base_affected;
            current_batch.taxes.push(tax_data);
        }

        if (current_batch !== null) {
            batches.push(current_batch);
        }

        for (const batch of batches) {
            const batch_indexes = batch.taxes.map((x) => x.index);
            batch.taxes = batch.taxes.toReversed();
            for (const tax_data of batch.taxes) {
                tax_data.batch_indexes = batch_indexes;
            }
        }

        return { batches, flatten_taxes_data }
    },

    /**
     * [!] Mirror of the same method in account_tax.py.
     * PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.
     */
    ascending_process_fixed_taxes_batch(batch) {
        const taxes_data = batch.taxes;
        const amount_type = batch.amount_type;

        if (amount_type === "fixed") {
            batch.is_tax_computed = true;
            for (const tax_data of taxes_data) {
                tax_data.evaluation_context.quantity_multiplicator = tax_data.amount * tax_data._factor;
            }
        } else if (amount_type === "percent") {
            let total_percentage = 0.0;
            for (const tax_data of taxes_data) {
                total_percentage += (tax_data.amount * tax_data._factor) / 100.0;
            }
            for (const tax_data of taxes_data) {
                const percentage = tax_data.amount / 100.0;
                tax_data.evaluation_context.incl_base_multiplicator = total_percentage != -1 ? 1 / (1 + total_percentage) : 0.0;
                tax_data.evaluation_context.excl_tax_multiplicator = percentage;
            }
        } else if (amount_type === "division") {
            let total_percentage = 0.0;
            for (const tax_data of taxes_data) {
                total_percentage += (tax_data.amount * tax_data._factor) / 100.0;
            }
            for (const tax_data of taxes_data) {
                const percentage = tax_data.amount / 100.0;
                const multiplicator = tax_data.evaluation_context.incl_base_multiplicator = 1 - total_percentage;
                const reverse_incl_base_multiplicator = multiplicator ? 1 / multiplicator : 0.0;
                tax_data.evaluation_context.excl_tax_multiplicator = multiplicator ? percentage / multiplicator : 0.0;
            }
        }
    },

    /**
     * [!] Mirror of the same method in account_tax.py.
     * PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.
     */
    descending_process_price_included_taxes_batch(batch) {
        const amount_type = batch.amount_type;
        const price_include = batch.price_include;

        if (!price_include) {
            return;
        }

        if (amount_type === "percent") {
            batch.is_base_computed = true;
            batch.is_tax_computed = true;
        } else if (amount_type === "division") {
            batch.is_base_computed = true;
            batch.is_tax_computed = true;
        } else if (amount_type === "fixed") {
            batch.is_base_computed = true;
        }
    },

    /**
     * [!] Mirror of the same method in account_tax.py.
     * PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.
     */
    ascending_process_taxes_batch(batch) {
        const amount_type = batch.amount_type;
        const price_include = batch.price_include;

        if (price_include) {
            return;
        }

        if (amount_type === "percent") {
            batch.is_base_computed = true;
            batch.is_tax_computed = true;
        } else if (amount_type === "division") {
            batch.is_base_computed = true;
            batch.is_tax_computed = true;
        } else if (amount_type === "fixed") {
            batch.is_base_computed = true;
        }
    },

    /**
     * [!] Mirror of the same method in account_tax.py.
     * PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.
     */
    prepare_taxes_computation(
        taxes_data,
        { is_refund = false, include_caba_tags = false, special_mode = false } = {}
    ) {

        // Group the taxes by batch of computation.
        const { batches, flatten_taxes_data } = this.prepare_taxes_batches(taxes_data, { special_mode: special_mode });
        const descending_batches = batches;
        const ascending_batches = descending_batches.toReversed();

        // First ascending computation for fixed tax.
        // In Belgium, we have a fixed price-excluded tax that affects the base of a 21% price-included tax.
        // In that case, we need to compute the fix amount before the descending computation.
        const eval_order_indexes = [];
        const ascending_extra_base = [];
        for (const batch of ascending_batches) {
            batch.ascending_extra_base = [...ascending_extra_base];

            this.ascending_process_fixed_taxes_batch(batch);

            // Build the expression representing the extra base as a sum.
            if (
                batch.is_tax_computed &&
                batch.include_base_amount &&
                !batch.price_include
            ) {
                for (const tax_data of batch.taxes) {
                    ascending_extra_base.push([1, tax_data.index]);
                }
            }

            if (batch.is_tax_computed) {
                for (const tax_data of batch.taxes) {
                    eval_order_indexes.push(["tax", tax_data.index]);
                }
            }
            if (batch.is_base_computed) {
                for (const tax_data of batch.taxes) {
                    eval_order_indexes.push(["base", tax_data.index]);
                }
            }
        }

        // First descending computation to compute price_included values.
        const descending_extra_base = [];
        for (const batch of descending_batches) {
            const is_base_computed = batch.is_base_computed;
            const is_tax_computed = batch.is_tax_computed;
            batch.descending_extra_base = [...descending_extra_base];

            // Build the expression representing the extra base as a sum.
            if (!is_base_computed) {
                batch.extra_base_for_base = descending_extra_base.concat(
                    batch.ascending_extra_base
                );
                batch.extra_base_for_tax = is_tax_computed ? [] : batch.extra_base_for_base;

                // Compute price-included taxes.
                this.descending_process_price_included_taxes_batch(batch);

                if (batch.is_base_computed) {
                    for (const tax_data of batch.taxes) {
                        descending_extra_base.push([-1, tax_data.index]);
                    }
                }

                if (batch.is_tax_computed && !is_tax_computed) {
                    for (const tax_data of batch.taxes) {
                        eval_order_indexes.push(["tax", tax_data.index]);
                    }
                }
                if (batch.is_base_computed) {
                    for (const tax_data of batch.taxes) {
                        eval_order_indexes.push(["base", tax_data.index]);
                    }
                }
            }
        }

        // Second ascending computation to compute the missing values for price-excluded taxes.
        // Build the final results.
        const extra_base = [];
        for (const [i, batch] of ascending_batches.entries()) {
            const is_base_computed = batch.is_base_computed;
            const is_tax_computed = batch.is_tax_computed;
            if (!is_base_computed) {
                // Build the expression representing the extra base as a sum.
                batch.extra_base_for_base = extra_base.concat(
                    batch.ascending_extra_base,
                    batch.descending_extra_base
                );
                batch.extra_base_for_tax = is_tax_computed ? [] : batch.extra_base_for_base;

                // Compute price-excluded taxes.
                this.ascending_process_taxes_batch(batch);

                // Update the base expression for the following taxes.
                if (!is_tax_computed && batch.include_base_amount) {
                    for (const tax_data of batch.taxes) {
                        extra_base.push([1, tax_data.index]);
                    }
                }

                if (batch.is_tax_computed && !is_tax_computed) {
                    for (const tax_data of batch.taxes) {
                        eval_order_indexes.push(["tax", tax_data.index]);
                    }
                }
                if (batch.is_base_computed) {
                    for (const tax_data of batch.taxes) {
                        eval_order_indexes.push(["base", tax_data.index]);
                    }
                }
            }

            // Compute the subsequent taxes / tags.
            const subsequent_tax_ids = [];
            const subsequent_tag_ids = new Set();
            const base_tags_field = is_refund ? "_refund_base_tag_ids" : "_invoice_base_tag_ids";
            if (batch.include_base_amount) {
                for (const next_batch of ascending_batches.toSpliced(0, i + 1)) {
                    for (const next_tax_data of next_batch.taxes) {
                        subsequent_tax_ids.push(next_tax_data.id);
                        if (include_caba_tags || next_tax_data.tax_exigibility !== "on_payment") {
                            for (const tag_id of next_tax_data[base_tags_field]) {
                                subsequent_tag_ids.add(tag_id);
                            }
                        }
                    }
                }
            }

            for (const tax_data of batch.taxes) {
                Object.assign(tax_data, {
                    tax_ids: subsequent_tax_ids,
                    tag_ids: [...subsequent_tag_ids],
                    extra_base_for_base: batch.extra_base_for_base,
                    extra_base_for_tax: batch.extra_base_for_tax,
                });
            }
        }

        return {
            taxes_data: flatten_taxes_data,
            eval_order_indexes: eval_order_indexes,
        };
    },

    // -------------------------------------------------------------------------
    // EVAL TAXES COMPUTATION
    // -------------------------------------------------------------------------

    /**
     * [!] Mirror of the same method in account_tax.py.
     * PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.
     */
    eval_taxes_computation_prepare_product_values(default_product_values, product) {
        const product_values = {};
        for (const [field_name, field_info] of Object.entries(default_product_values)) {
            product_values[field_name] = product
                ? product[field_name] || field_info.default_value
                : field_info.default_value;
        }
        return product_values;
    },

    /**
     * [!] Mirror of the same method in account_tax.py.
     * PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.
     */
    eval_taxes_computation_prepare_context(
        price_unit,
        quantity,
        product_values,
        { rounding_method = "round_per_line", precision_rounding = 0.01 } = {}
    ) {
        return {
            product: product_values,
            price_unit: price_unit,
            quantity: quantity,
            rounding_method: rounding_method,
            precision_rounding: rounding_method === "round_globally" ? null : precision_rounding,
        };
    },

    /**
     * [!] Mirror of the same method in account_tax.py.
     * PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.
     */
    eval_tax_amount(tax_data, evaluation_context) {
        const amount_type = tax_data.amount_type;
        const special_mode = evaluation_context.special_mode;
        const price_include = tax_data.price_include;

        if (amount_type === "fixed") {
            return evaluation_context.quantity * evaluation_context.quantity_multiplicator;
        }

        let raw_base =
            evaluation_context.quantity * evaluation_context.price_unit +
            evaluation_context.extra_base;
        if ("incl_base_multiplicator" in evaluation_context && ((price_include && !special_mode) || special_mode === "total_included")) {
            raw_base *= evaluation_context.incl_base_multiplicator;
        }

        if ("excl_tax_multiplicator" in evaluation_context){
            return raw_base * evaluation_context.excl_tax_multiplicator;
        }
        return 0.0;
    },

    /**
     * [!] Mirror of the same method in account_tax.py.
     * PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.
     */
    eval_tax_base_amount(tax_data, evaluation_context) {
        const price_include = tax_data.price_include;
        const amount_type = tax_data.amount_type;
        const total_tax_amount = evaluation_context.total_tax_amount;
        const special_mode = evaluation_context.special_mode;

        let raw_base =
            evaluation_context.quantity * evaluation_context.price_unit +
            evaluation_context.extra_base;

        if (price_include) {
            let base = special_mode === "total_excluded" ? raw_base : raw_base - total_tax_amount;
            if (amount_type === "division") {
                return {
                    base: base,
                    display_base: raw_base,
                    display_base_type: "total_included",
                };
            } else if (amount_type === "fixed") {
                return {
                    base: base,
                    display_base: null,
                    display_base_type: "same_base",
                };
            } else {
                return {
                    base: base,
                };
            }
        } else if(special_mode === "total_included") {
            raw_base -= total_tax_amount;
        }

        if (amount_type === "fixed") {
            return {
                base: raw_base,
                display_base: null,
                display_base_type: "same_base",
            };
        }

        // Price excluded.
        return {
            base: raw_base,
        };
    },

    /**
     * [!] Mirror of the same method in account_tax.py.
     * PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.
     */
    eval_taxes_computation(taxes_computation, evaluation_context) {
        const taxes_data = taxes_computation.taxes_data;
        const eval_order_indexes = taxes_computation.eval_order_indexes;
        const rounding_method = evaluation_context.rounding_method;
        const prec_rounding = evaluation_context.precision_rounding;
        let eval_taxes_data = taxes_data.map((tax_data) =>
            Object.assign({}, tax_data)
        );
        const skipped = new Set();
        for (const [quid, index] of eval_order_indexes) {
            const tax_data = eval_taxes_data[index];
            const special_mode = tax_data.evaluation_context.special_mode;
            if (quid === "tax") {
                let extra_base = 0.0;
                for (const [extra_base_sign, extra_base_index] of tax_data.extra_base_for_tax) {
                    const target_tax_data = eval_taxes_data[extra_base_index];
                    if (special_mode !== "total_excluded" || !target_tax_data.price_include) {
                        extra_base += extra_base_sign * target_tax_data.tax_amount_factorized;
                    }
                }
                let tax_amount = this.eval_tax_amount(tax_data, {
                    ...evaluation_context,
                    ...tax_data.evaluation_context,
                    extra_base: extra_base,
                });
                if (tax_amount === undefined) {
                    skipped.add(tax_data.id);
                    tax_amount = 0.0;
                }
                tax_data.tax_amount = tax_amount;
                tax_data.tax_amount_factorized = tax_data.tax_amount * tax_data._factor;
                if (rounding_method === "round_per_line") {
                    tax_data.tax_amount_factorized = roundPrecision(
                        tax_data.tax_amount_factorized,
                        prec_rounding
                    );
                }
            } else if (quid === "base") {
                let extra_base = 0.0;
                for (const [extra_base_sign, extra_base_index] of tax_data.extra_base_for_base) {
                    const target_tax_data = eval_taxes_data[extra_base_index];
                    if (special_mode !== "total_excluded" || !target_tax_data.price_include) {
                        extra_base += extra_base_sign * target_tax_data.tax_amount_factorized;
                    }
                }
                let total_tax_amount = 0.0;
                for (const batch_index of tax_data.batch_indexes) {
                    total_tax_amount += eval_taxes_data[batch_index].tax_amount_factorized;
                }
                Object.assign(
                    tax_data,
                    this.eval_tax_base_amount(tax_data, {
                        ...evaluation_context,
                        ...tax_data.evaluation_context,
                        extra_base: extra_base,
                        total_tax_amount: total_tax_amount,
                    })
                );
                if (!("display_base" in tax_data)){
                    if(!("display_base_type" in tax_data)){
                        tax_data.display_base_type = "same_base";
                    }
                    if(tax_data.display_base_type === "same_base"){
                        tax_data.display_base = tax_data.base;
                    }
                }
                if (rounding_method === "round_per_line") {
                    tax_data.base = roundPrecision(
                        tax_data.base,
                        prec_rounding
                    );
                    if(tax_data.display_base){
                        tax_data.display_base = roundPrecision(
                            tax_data.display_base,
                            prec_rounding
                        );
                    }
                }
            }
        }

        if (skipped.length > 0) {
            eval_taxes_data = eval_taxes_data.filter(
                (tax_data) => !skipped.has(tax_data.id)
            );
        }

        let total_excluded = null;
        let total_included = null;
        if (eval_taxes_data.length > 0) {
            total_excluded = eval_taxes_data[0].base;
            let tax_amount = 0.0;
            for (const tax_data of eval_taxes_data) {
                tax_amount += tax_data.tax_amount_factorized;
            }
            total_included = total_excluded + tax_amount;
        } else {
            total_excluded = total_included =
                evaluation_context.quantity * evaluation_context.price_unit;
            if (rounding_method === "round_per_line") {
                total_excluded = total_included = roundPrecision(total_excluded, prec_rounding);
            }
        }

        const tax_details = {};
        for(const tax_data of eval_taxes_data){
            tax_details[tax_data.id] = {
                tax_amount: tax_data.tax_amount_factorized,
                base: tax_data.base,
                display_base: tax_data.display_base,
                display_base_type: tax_data.display_base_type,
            };
        }
        return {
            taxes_data: eval_taxes_data,
            total_excluded: total_excluded,
            total_included: total_included,
            tax_details: tax_details,
        };
    },

    // -------------------------------------------------------------------------
    // EVAL TAXES COMPUTATION
    // -------------------------------------------------------------------------

    adapt_price_unit_to_another_taxes(
        price_unit,
        product_values,
        original_taxes_data,
        new_taxes_data
    ) {
        const original_tax_ids = new Set(original_taxes_data.map((x) => x.id));
        const new_tax_ids = new Set(new_taxes_data.map((x) => x.id));
        if (
            (original_tax_ids.size === new_tax_ids.size &&
                [...original_tax_ids].every((value) => new_tax_ids.has(value))) ||
            original_taxes_data.some((x) => !x.price_include)
        ) {
            return price_unit;
        }

        let taxes_computation = this.prepare_taxes_computation(original_taxes_data);
        let evaluation_context = this.eval_taxes_computation_prepare_context(
            price_unit,
            1.0,
            product_values,
            { rounding_method: "round_globally" }
        );
        taxes_computation = this.eval_taxes_computation(taxes_computation, evaluation_context);
        price_unit = taxes_computation.total_excluded;

        taxes_computation = this.prepare_taxes_computation(new_taxes_data, { special_mode: "total_excluded" });
        evaluation_context = this.eval_taxes_computation_prepare_context(
            price_unit,
            1.0,
            product_values,
            { rounding_method: "round_globally" }
        );
        taxes_computation = this.eval_taxes_computation(taxes_computation, evaluation_context);
        let delta = 0.0;
        for (const tax_data of taxes_computation.taxes_data) {
            if (tax_data.price_include) {
                delta += tax_data.tax_amount_factorized;
            }
        }
        return price_unit + delta;
    },

    // -------------------------------------------------------------------------
    // GENERIC REPRESENTATION OF BUSINESS OBJECTS
    // -------------------------------------------------------------------------

    create_document_for_taxes_computation(
        currency_id,
        precision_rounding,
        { rounding_method: "round_per_line" } = {}
    ) {
        return {
            currency_id: currency_id,
            rounding_method: rounding_method,
            precision_rounding: precision_rounding,
            precision_digits: Math.round(Math.abs(Math.log10(precision_rounding))),
        };
    }

    create_document_line(
        price_unit,
        quantity,
        discount,
        { product_values: null,  taxes_data: null, tax_details: null} = {}
    ) {
        const discounted_price_unit = price_unit * (1 - discount / 100.0);
        const line = {
            price_unit: price_unit,
            discounted_price_unit: discounted_price_unit,
            quantity: quantity,
            discount: discount,
            product_values: product_values || {},
            taxes_data: taxes_data || [],
        };

        if (tax_details !== null) {
            line.tax_details = tax_details;
        }

        return line;
    }

    add_cash_rounding_to_document(
        document_values,
        strategy,
        precision_rounding,
        { rounding_method: "HALF-UP" } = {}
    ) {
        document_values.cash_rounding = {
            strategy: strategy,
            precision_rounding: precision_rounding,
            rounding_method: rounding_method,
        };
    }

    add_line_tax_amounts_to_document(document_values) {
        for(const line of document_values.lines) {
            if (!("tax_details" in line)){
                const evaluation_context = eval_taxes_computation_prepare_context(
                    line.discounted_price_unit,
                    line.quantity,
                    line.product_values,
                    {
                        rounding_method: document_values.rounding_method,
                        precision_rounding: document_values.precision_rounding,
                    }
                );

                const taxes_computation = eval_taxes_computation(
                    prepare_taxes_computation(line.taxes_data),
                    evaluation_context
                );
            }

            const tax_details = line.tax_details;
            let total_excluded = null;
            let total_included = null;
            if(tax_details.size > 0){
                const tax_details_values = Object.values(tax_details);
                total_excluded = tax_details_values[0].base;
                const tax_amount = tax_details_values.reduce((acc, tax_data) => acc + tax_data.tax_amount);
                total_included = total_excluded + tax_amount;
            }else{
                total_excluded = total_included = line.quantity * line.discounted_price_unit;
            }
            line.total_included = roundPrecision(total_included, document_values.precision_rounding);
            line.total_excluded = roundPrecision(total_excluded, document_values.precision_rounding);
        }
    }

    // -------------------------------------------------------------------------
    // DISCOUNT
    // -------------------------------------------------------------------------

    prepare_document_global_discount_percentage_line(document_values, line, factor_percent) {
        const total_included = line.total_included;
        const new_taxes_data = line.taxes_data.filter(x => x._is_discountable);
        const evaluation_context = eval_taxes_computation_prepare_context(
            -factor_percent * total_included,
            1.0,
            line.product_values,
            { rounding_method: "round_globally" }
        );

        const taxes_computation = eval_taxes_computation(
            prepare_taxes_computation(line.taxes_data, { special_mode: "total_included" }),
            evaluation_context
        );

        return prepare_document_line({
            price_unit: taxes_computation.total_excluded,
            quantity: 1.0,
            discount: 0.0,
            taxes_data: new_taxes_data,
            tax_details: taxes_computation.tax_details
        });
    }

    // -------------------------------------------------------------------------
    // TAXES AGGREGATOR
    // -------------------------------------------------------------------------

    aggregate_display_bases(display_bases, { keep_first_base: false } = {}) {
        const all_null_display_base = (display_bases) => {
            return display_bases.every([display_base, _base, _display_base_type] => display_base === null);
        }

        const all_same_base = (display_bases) => {
            return display_bases.every(([_display_base, _base, display_base_type]) => display_base_type === 'same_base');
        }

        const all_same_display_base_type = (display_bases) => {
            const display_base_types = new Set();
            for (const [_display_base, _base, display_base_type] of display_bases){
                display_base_types.add((display_base == null, display_base_type));
            }

        }

        if (all_null_display_base(display_bases)) {
            // Nothing to display for this group.
            return [null, null, null];
        } else if (all_same_base(display_bases)) {
            let display_base_amount;
            if (keep_first_base) {
                const [display_base, base, _display_base_type] = display_bases[0];
                display_base_amount = display_base == null ? base : display_base;
            } else {
                display_base_amount = display_bases.reduce((acc, [display_base, base]) => acc + (display_base === null ? base : display_base), 0);
            }
            return [display_base_amount, display_base_amount, 'same_base'];
        } else if (new Set(display_bases.map(([display_base, _base, display_base_type]) => [display_base === null, display_base_type])).size === 1) {
            // All have the same display_base_type, aggregate them.
            const display_base_type = display_bases[0][2];
            let base;
            if (keep_first_base) {
                [_, base] = display_bases[0];
            } else {
                base = display_bases.reduce((acc, [display_base, base]) => acc + base, 0);
            }
            if (display_bases.some(([display_base]) => display_base === null)) {
                return [null, base, display_base_type];
            } else if (keep_first_base) {
                return [display_bases[0][0], base, display_base_type];
            } else {
                const display_base_amount = display_bases.reduce((acc, [display_base]) => acc + display_base, 0);
                return [display_base_amount, base, display_base_type];
            }
        } else {
            // Not able to aggregate them.
            return [null, null, null];
        }
    }

    aggregate_document_taxes(document_values, grouping_key_function, { aggregate_function = null} = {}) {
        const results = {
            untaxed_amount: document_values.lines.reduce((acc, line) => acc + line.total_excluded, 0),
            subtotals: {},
        };
        const subtotals = results.subtotals;

        const amounts_per_grouping_key = {};
        document_values.lines.forEach((line, i) => {
            const tax_details = line.tax_details;

            const [_batches, taxes_data] = prepare_taxes_batches(line.taxes_data);

            const encountered_grouping_keys = new Set();
            taxes_data.forEach(tax_data => {
                tax_data = Object.assign(tax_data, tax_details[tax_data.id]);

                const grouping_key = JSON.stringify(grouping_key_function(line, tax_data));
                if (!subtotals[grouping_key]) {
                    subtotals[grouping_key] = {
                        tax_amount: 0.0,
                        base: 0.0,
                        display_base: {},
                    };
                    if (aggregate_function) {
                        aggregate_function(line, tax_data, subtotals[grouping_key]);
                    }
                }

                const subtotal = subtotals[grouping_key];

                if (!(tax_data.id in amounts_per_grouping_key)) {
                    const amounts = amounts_per_grouping_key[tax_data.id] = {
                        base: 0.0,
                        tax_amount: 0.0,
                        lines: {},
                    };
                    if (!(i in amounts.lines)){
                        amounts.lines[i] = {
                            base: 0.0,
                            tax_amount: 0.0,
                            tax_grouping_keys: new Set(),
                            base_grouping_keys: new Set(),
                        };
                    }
                }

                // Track the tax amount.
                amounts_per_grouping_key[tax_data.id].tax_amount += Math.abs(tax_data.tax_amount);
                amounts_per_grouping_key[tax_data.id].lines[i].tax_amount += tax_data.tax_amount;
                amounts_per_grouping_key[tax_data.id].lines[i].tax_grouping_keys.add(grouping_key);

                // Track the base amount.
                amounts_per_grouping_key[tax_data.id].base += Math.abs(tax_data.base);
                amounts_per_grouping_key[tax_data.id].lines[i].base += tax_data.base;
                if (!encountered_grouping_keys.has(grouping_key)) {
                    encountered_grouping_keys.add(grouping_key);
                    amounts_per_grouping_key[tax_data.id].lines[i].base_grouping_keys.add(grouping_key);
                }

                // Track the display_base amount.
                if (!(i in subtotal.display_base[i])) {
                    subtotal.display_base[i] = [];
                }
                subtotal.display_base[i].push([
                    tax_data.display_base,
                    tax_data.base,
                    tax_data.display_base_type,
                ]);
            });
        });

        // Process 'tax_amount'.
        for (const total of Object.values(amounts_per_grouping_key)) {
            let total_amount = roundPrecision(
                total.base + total.tax_amount,
                document_values.precision_rounding
            );
            let total_rounded_tax_amount = roundPrecision(
                total.tax_amount,
                document_values.precision_rounding
            );
            let total_rounded_base_amount = roundPrecision(
                total_amount - total.tax_amount,
                document_values.precision_rounding
            );

            for (const [i, line_total] of Object.entries(total.lines)) {
                const is_last_line = i === total.lines.size - 1;
                let line_rounded_tax_amount = null;
                let line_rounded_base_amount = null;
                if (is_last_line) {
                    let sign = line_total.tax_amount > 0.0 ? 1 : -1;
                    line_rounded_tax_amount = sign * total_rounded_tax_amount;
                    sign = line_total.base > 0.0 ? 1 : -1;
                    line_rounded_base_amount = sign * total_rounded_base_amount;
                } else {
                    line_rounded_tax_amount = roundPrecision(
                        line_total.tax_amount,
                        document_values.precision_rounding
                    );
                    line_rounded_base_amount = roundPrecision(
                        line_total.base,
                        document_values.precision_rounding
                    );
                }
                total_rounded_tax_amount -= Math.abs(line_rounded_tax_amount);
                total_rounded_base_amount -= Math.abs(line_rounded_base_amount);
                line_total.tax_amount = line_rounded_tax_amount;
                line_total.base = line_rounded_base_amount;

                // Dispatch per grouping_key.
                line_total.tax_grouping_keys.forEach(grouping_key => {
                    subtotals[grouping_key].tax_amount += line_total.tax_amount;
                });
                line_total.base_grouping_keys.forEach(grouping_key => {
                    subtotals[grouping_key].base += line_total.base;
                });
            }
        }

        // Process 'display_base'.
        function aggregate_display_bases(display_bases, keep_first_base=false) {
            if (display_bases.every(([display_base, _base, _display_base_type]) => display_base === null)) {
                return [null, null, null];
            } else if (display_bases.every(([_, _base, display_base_type]) => display_base_type === 'same_base')) {
                let display_base_amount;
                if (keep_first_base) {
                    display_base_amount = display_bases[0][1];
                } else {
                    display_base_amount = display_bases.reduce((acc, [_display_base, base, _]) => acc + base, 0);
                }
                return [display_base_amount, display_base_amount, 'same_base'];
            } else if (display_bases.every(([display_base, _base, display_base_type]) => display_base === null || display_base_type === 'same_base')) {
                let display_base_type = display_bases[0][2];
                let base;
                if (keep_first_base) {
                    base = display_bases[0][1];
                } else {
                    base = display_bases.reduce((acc, [_display_base, base, _]) => acc + base, 0);
                }
                if (display_bases.some(([display_base, _, __]) => display_base === null)) {
                    return [null, base, display_base_type];
                } else if (keep_first_base) {
                    return [display_bases[0][0], base, display_base_type];
                } else {
                    let display_base_amount = display_bases.reduce((acc, [display_base, _, __]) => acc + display_base, 0);
                    return [display_base_amount, base, display_base_type];
                }
            } else {
                return [null, null, null];
            }
        }

        for (const subtotal of Object.values(subtotals)) {
            const display_bases = [];
            for (const line_display_bases of Object.values(subtotal.display_base)) {
                display_bases.push(aggregate_display_bases(line_display_bases, true));
            }

            const [display_base, _, display_base_type] = aggregate_display_bases(display_bases);
            subtotal.display_base = display_base;
            subtotal.display_base_type = display_base_type;
            if (subtotal.display_base !== null) {
                subtotal.display_base = floatRound(
                    subtotal.display_base,
                    { precisionRounding: document_values.precision_rounding }
                );
            }
        }

        results.tax_amount = 0.0;

        // Process 'base'.
        for (const subtotal of Object.values(subtotals)) {
            if (subtotal.display_base_type === 'same_base') {
                subtotal.display_base = subtotal.base;
            }
            results.tax_amount += subtotal.tax_amount;
        }

        // Total amounts.
        results.total_amount = results.untaxed_amount + results.tax_amount;

        return results;
    }

    }

};

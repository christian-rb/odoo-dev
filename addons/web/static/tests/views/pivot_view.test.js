/** @odoo-module */

import { expect, test } from "@odoo/hoot";
import { queryAll, queryAllTexts, queryFirst } from "@odoo/hoot-dom";
import {
	defineModels,
	fields,
	models,
	onRpc,
	mountView,
	contains,
	getService,
	mountWithCleanup,
	toggleMenuItem,
	toggleSearchBarMenu,
	patchDate,
} from "@web/../tests/web_test_helpers";
import { WebClient } from "@web/webclient/webclient";


class Partner extends models.Model {
	_name = "partner";
	foo = fields.Integer({ string: "Foo", searchable: true, aggregator: "sum" });
	bar = fields.Boolean({ string: "bar", store: true, sortable: true, groupable: true });
	date = fields.Date({ string: "Date", store: true, groupable: true, sortable: true });
	product_id = fields.Many2one({ string: "Product", relation: "product", store: true, sortable: true, groupable: true });
	other_product_id = fields.Many2one({ string: "Other Product", relation: "product", store: true, sortable: true, groupable: true });
	non_stored_m2o = fields.Many2one({ string: "Non Stored M2O", relation: "product" });
	customer = fields.Many2one({ string: "Customer", store: true, relation: "customer", store: true, sortable: true, groupable: true });
	computed_field = fields.Integer({ string: "Computed and not stored", compute: true, aggregator: "sum" });
	company_type = fields.Selection({ string: "Company Type", selection: [["company", "Company"], ["individual", "individual"]], searchable: true, sortable: true, store: true, groupable: true });
	price_nonaggregatable = fields.Monetary({ string: "Price non-aggregatable", aggregator: undefined, store: true, currency_field: this.currency_id });
	ref = fields.Reference({
		string: "Reference", selection: [
			["product", "Product"],
			["customer", "Customer"],
		], aggregator: "count_distinct"
	})
	properties = fields.Properties({ string: "Properties", definition_record: "parent_id", definition_record_field: "properties_defintion" })
	parent_id = fields.Many2one({ string: "Parent", relation: "partner" });
	properties_definition = fields.PropertiesDefinition({ string: "Properties" });
	display_name = fields.Char({ string: "Displayed name" });
	_records = [
		{
			id: 1,
			foo: 12,
			bar: true,
			date: "2016-12-14",
			product_id: 37,
			customer: 1,
			computed_field: 19,
			company_type: "company",
			ref: "product,37",
			properties_definition: [
				{
					name: "my_char",
					string: "My Char",
					type: "char",
				},
			],
		},
		{
			id: 2,
			foo: 1,
			bar: true,
			date: "2016-10-26",
			product_id: 41,
			customer: 2,
			computed_field: 23,
			company_type: "individual",
			ref: "product,41",
			parent_id: 1,
			properties: [
				{
					name: "my_char",
					string: "My Char",
					type: "char",
					value: "aaa",
				},
			],
		},
		{
			id: 3,
			foo: 17,
			bar: true,
			date: "2016-12-15",
			product_id: 41,
			customer: 2,
			computed_field: 26,
			company_type: "company",
			ref: "customer,1",
			parent_id: 1,
			properties: [
				{
					name: "my_char",
					string: "My Char",
					type: "char",
					value: "bbb",
				},
			],
		},
		{
			id: 4,
			foo: 2,
			bar: false,
			date: "2016-04-11",
			product_id: 41,
			customer: 1,
			computed_field: 19,
			company_type: "individual",
			ref: "customer,2",
		},
	];
}

class Product extends models.Model {
	_name = "product";
	name = fields.Char({ string: "Product Name" });
	_records = [
		{
			id: 37,
			name: "xphone",
		},
		{
			id: 41,
			name: "xpad",
		},
	];
}

class Customer extends models.Model {
	_name = "customer";
	name = fields.Char({ string: "Customer Name" });
	_records = [
		{
			id: 1,
			name: "First",
		},
		{
			id: 2,
			name: "Second",
		},
	];
}

defineModels([Partner, Product, Customer]);

test("simple pivot rendering", async () => {
	expect.assertions(4);
	onRpc("read_group", ({ kwargs }) => {
		expect(kwargs.lazy).toBe(false);
	});

	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot string="Partners">
				<field name="foo" type="measure"/>
			</pivot>
		`,
	});

	expect(".o_pivot_view").toHaveClass("o_view_controller");
	expect("table").toHaveClass("o_enable_linking");
	expect("td.o_pivot_cell_value:contains(32)").toHaveCount(1);
});

test("all measures should be displayed with a pivot_measures context", async () => {
	Partner._fields.bouh = fields.Integer({ string: "bouh", aggregator: "sum" });

	await mountView({
		type: "pivot",
		resModel: "partner",
		context: { pivot_measures: ["foo"] },
		arch: `
			<pivot string="Partners">
				<field name="foo" type="measure"/>
				<field name="bouh" type="measure"/>
			</pivot>
			`,
	});

	await contains("button:contains(Measures)").click();
	expect(".o_popover.popover.o-dropdown--menu.dropdown-menu").toHaveCount(1);
	const measures = queryAllTexts(".o-dropdown-item");
	expect(measures).toEqual(["bouh", "Computed and not stored", "Foo", "Count"]);
});

test("pivot rendering with widget", async () => {
	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot string="Partners">
				<field name="foo" type="measure" widget="float_time"/>
			</pivot>
		`,
	});
	expect("td.o_pivot_cell_value:contains(32:00)").toHaveCount(1);
});

test("pivot rendering with string attribute on field", async () => {
	Partner._fields.foo = fields.Integer({ string: "Foo", store: true, aggregator: "sum" });

	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot string="Partners">
				<field name="foo" string="BAR" type="measure"/>
			</pivot>
		`,
	});

	const toggler = ".o_pivot_buttons button.dropdown-toggle";
	await contains(toggler).click();
	expect(".o-dropdown-item:first").toHaveText("BAR");
	expect(".o_pivot_measure_row").toHaveText("BAR");
});

test("Pivot with integer row group by with 0 as header", async () => {
	Partner._records[0].foo = 0;
	Partner._records[1].foo = 0;
	Partner._records[2].foo = 0;
	Partner._records[3].foo = 0;

	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot string="Partners">
				<field name="foo" type="measure"/>
				<field name="foo" type="row"/>
			</pivot>
		`,
	});
	expect(".o_pivot table tr td.o_pivot_cell_value").toHaveCount(2);
	expect(".o_pivot table tbody tr:eq(0) th:eq(0)").toHaveText("Total");
	expect(".o_pivot table tbody tr:eq(0) td:eq(0)").toHaveText("0");
});

test("Pivot with integer col group by with 0 as header", async () => {
	Partner._records[0].foo = 0;
	Partner._records[1].foo = 0;
	Partner._records[2].foo = 0;
	Partner._records[3].foo = 0;
	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot string="Partners">
				<field name="foo" type="measure"/>
				<field name="foo" type="col"/>
			</pivot>`,
	});
	expect(".o_pivot table thead tr:eq(1) th").toHaveText("0");
});

test("pivot rendering with string attribute on non stored field", async () => {
	Partner._fields.fubar = fields.Integer({
		string: "Fubar",
		store: false,
		aggregator: "sum",
	});
	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot string="Partners">
				<field name="fubar" string="fubar" type="measure"/>
			</pivot>
		`,
	});
	expect(".o_pivot table thead tr:eq(1) th").toHaveText("fubar");
});

test("pivot rendering with invisible attribute on field", async () => {
	// when invisible, a field should neither be an active measure nor be a selectable measure
	Partner._fields.foo = fields.Integer({ string: "Foo", store: true, aggregator: "sum" });
	Partner._fields.foo2 = fields.Integer({ string: "Foo2", store: true, aggregator: "sum" });
	Partner._fields.computed_field = fields.Integer({ string: "Computed and not stored", compute: true, aggregator: null });

	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot string="Partners">
				<field name="foo" type="measure"/>
				<field name="foo2" type="measure" invisible="1"/>
			</pivot>
		`,
	});

	// there should be only one displayed measure as the other one is invisible
	expect(".o_pivot_measure_row").toHaveCount(1);
	await contains(".o_pivot_buttons button.dropdown-toggle").click();
	// there should be only one measure besides count, as the other one is invisible
	expect(".dropdown-item").toHaveCount(2);
	expect(".dropdown-item:first").toHaveText("Foo");
	// the invisible field souldn't be in the groupable fields neither
	await contains(".o_pivot_header_cell_closed").click();
	expect('.o-dropdown--menu a[data-field="foo2"]').toHaveCount(0);
});

test("group headers should have a tooltip", async () => {
	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot>
				<field name="product_id" type="col"/>
				<field name="date" type="row"/>
			</pivot>
		`,
	});

	expect(queryAll("tbody .o_pivot_header_cell_closed").at(0).dataset.tooltip).toBe("Date");
	expect(queryAll("thead .o_pivot_header_cell_closed").at(1).dataset.tooltip).toBe("Product");
});

test(
	"pivot view add computed fields explicitly defined as measure",
	async () => {
		await mountView({
			type: "pivot",
			resModel: "partner",
			arch: `
			<pivot>
				<field name="computed_field" type="measure"/>
			</pivot>`,
		});

		await contains(".o_pivot_buttons button.dropdown-toggle").click();
		expect(".dropdown-item:contains(Computed and not stored)").toHaveCount(1);
		expect(".o_pivot_measure_row").toHaveText("Computed and not stored");
	}
);

test(
	"pivot view do not add number field without aggregator",
	async () => {
		await mountView({
			type: "pivot",
			resModel: "partner",
			arch: `
			<pivot>
				<field name="price_nonaggregatable"/>
			</pivot>`,
		});
		await contains(".o_pivot_buttons button.dropdown-toggle").click();
		expect(".dropdown-item:contains(Price non-aggregatable)").toHaveCount(0);
	}
);

// test.debug("clicking on a cell triggers a doAction", async function (assert) {
// 	expect.assertions(2);
// 	Partner._views["form, 2"] = `<form/>`;
// 	Partner._views["list, false"] = `<list/>`;
// 	Partner._views["kanban, 5"] = `<kanban/>`;

// 	// onRpc(({ method }) => expect.step(method));

// 	await mountWithCleanup(WebClient);
// 	getService("action").doAction({
// 		context: {
// 			lang: "en",
// 			tz: "taht",
// 			someKey: true,
// 			uid: 7,
// 			userContextKey: true,
// 		},
// 		domain: [["product_id", "=", 37]],
// 		name: "Partners",
// 		res_model: "partner",
// 		target: "current",
// 		type: "ir.actions.act_window",
// 		view_mode: "list",
// 		views: [
// 			[false, "list"],
// 			[2, "form"],
// 		],
// 	});

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
// 		arch: `
// 			<pivot string="Partners">
// 				<field name="product_id" type="row"/>
// 				<field name="foo" type="measure"/>
// 			</pivot>`,
// 		context: { someKey: true, search_default_test: 3 },
// 		config: {
// 			views: [
// 				[2, "form"],
// 				[5, "kanban"],
// 				[false, "list"],
// 				[false, "pivot"],
// 			],
// 		},
// 	});

// 	expect("table").toHaveClass("o_enable_linking");
// 	await contains(".o_pivot_cell_value:eq(1)").click(); // should trigger a do_action
// });

test("row and column are highlighted when hovering a cell", async () => {
	expect.assertions(11);

	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot string="Partners">
				<field name="foo" type="col"/>
				<field name="product_id" type="row"/>
			</pivot>`,
	});

	// check row highlighting
	expect("table").toHaveClass("table-hover");

	// check column highlighting
	// hover third measure
	await contains("th.o_pivot_measure_row:nth-of-type(3)").hover();
	expect(".o_cell_hover").toHaveCount(3);
	for (var i = 1; i <= 3; i++) {
		expect(`tbody tr:nth-of-type(${i}) td:nth-of-type(3)`).toHaveClass("o_cell_hover");
	}
	await contains(".o_pivot_buttons button.dropdown-toggle").hover();
	expect(".o_cell_hover").toHaveCount(0);

	// hover second cell, second row
	await contains("tbody tr:nth-of-type(1) td:nth-of-type(2)").hover();
	expect(".o_cell_hover").toHaveCount(3);
	for (i = 1; i <= 3; i++) {
		expect(`tbody tr:nth-of-type(${i}) td:nth-of-type(2)`).toHaveClass("o_cell_hover");
	}
	await contains(".o_pivot_buttons button.dropdown-toggle").hover();
	expect(".o_cell_hover").toHaveCount(0);
});

test("columns are highlighted when hovering a measure", async () => {
	expect.assertions(15);

	patchDate("2016-12-20T1:00:00");
	Partner._records[0].date = "2016-11-15";
	Partner._records[1].date = "2016-12-17";
	Partner._records[2].date = "2016-11-22";
	Partner._records[3].date = "2016-11-03";

	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot>
				<field name="product_id" type="row"/>
				<field name="date" type="col"/>
			</pivot>`,
		searchViewArch: `
			<search>
				<filter name="date_filter" date="date" domain="[]" default_period='this_month'/>
			</search>`,
		context: { search_default_date_filter: true },
	});

	await toggleSearchBarMenu();
	await toggleMenuItem("Date: Previous period");

	// hover Count in first group
	await contains("th.o_pivot_measure_row:nth-of-type(1)").hover();
	expect(".o_cell_hover").toHaveCount(3);
	for (let i = 1; i <= 3; i++) {
		expect(`tbody tr:nth-of-type(${i}) td:nth-of-type(1)`).toHaveClass("o_cell_hover");
	}
	await contains(".o_pivot_buttons button.dropdown-toggle").hover();
	expect(".o_cell_hover").toHaveCount(0);

	// hover Count in second group
	await contains("th.o_pivot_measure_row:nth-of-type(2)").hover();
	expect(".o_cell_hover").toHaveCount(3);
	for (let i = 1; i <= 3; i++) {
		expect(`tbody tr:nth-of-type(${i}) td:nth-of-type(4)`).toHaveClass("o_cell_hover");
	}
	await contains(".o_pivot_buttons button.dropdown-toggle").hover();
	expect(".o_cell_hover").toHaveCount(0);

	// hover Count in total column
	await contains("th.o_pivot_measure_row:nth-of-type(3)").hover();
	expect(".o_cell_hover").toHaveCount(3);
	for (let i = 1; i <= 3; i++) {
		expect(`tbody tr:nth-of-type(${i}) td:nth-of-type(7)`).toHaveClass("o_cell_hover");
	}
	await contains(".o_pivot_buttons button.dropdown-toggle").hover();
	expect(".o_cell_hover").toHaveCount(0);
});

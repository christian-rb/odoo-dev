/** @odoo-module */

import { expect, test } from "@odoo/hoot";
import { queryAll, queryAllTexts, queryOne, queryText } from "@odoo/hoot-dom";
import {
	defineModels,
	fields,
	models,
	onRpc,
	mountView,
	contains,
	toggleMenuItem,
	toggleSearchBarMenu,
	patchDate,
	mockService,
	getDropdownMenu,
} from "@web/../tests/web_test_helpers";


class Partner extends models.Model {
	_name = "partner";
	foo = fields.Integer({ string: "Foo", searchable: true, aggregator: "sum", groupable: false,});
	bar = fields.Boolean({ string: "bar", store: true, sortable: true, groupable: true });
	date = fields.Date({ string: "Date", store: true, groupable: true, sortable: true });
	product_id = fields.Many2one({ string: "Product", relation: "product", store: true, sortable: true, groupable: true });
	other_product_id = fields.Many2one({ string: "Other Product", relation: "product", store: true, sortable: true, groupable: true });
	non_stored_m2o = fields.Many2one({ string: "Non Stored M2O", relation: "product", groupable: false});
	customer = fields.Many2one({ string: "Customer", store: true, relation: "customer", store: true, sortable: true, groupable: true });
	computed_field = fields.Integer({ string: "Computed and not stored", compute: true, aggregator: "sum", groupable: false});
	company_type = fields.Selection({ string: "Company Type", selection: [["company", "Company"], ["individual", "individual"]], searchable: true, sortable: true, store: true, groupable: true });
	price_nonaggregatable = fields.Monetary({ string: "Price non-aggregatable", aggregator: undefined, store: true, currency_field: this.currency_id, groupable: false,});
	ref = fields.Reference({
		string: "Reference", selection: [
			["product", "Product"],
			["customer", "Customer"],
		], aggregator: "count_distinct"
	})
	properties = fields.Properties({ string: "Properties", definition_record: "parent_id", definition_record_field: "properties_defintion" })
	parent_id = fields.Many2one({ string: "Parent", relation: "partner", groupable: false,});
	properties_definition = fields.PropertiesDefinition({ string: "Properties", groupable: false,});
	display_name = fields.Char({ string: "Displayed name", groupable: false});
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

// test.debug("clicking on a cell triggers a doAction", async () => {
// 	expect.assertions(2);
// 	Partner._views["form, 2"] = `<form/>`;
// 	Partner._views["list, false"] = `<list/>`;
// 	Partner._views["kanban, 5"] = `<kanban/>`;

// 	mockService("action", () => {
// 		return {
// 			doAction(action) {
// 				expect(action).toEqual(
// 					{
// 						context: {
// 							lang: "en",
// 							tz: "taht",
// 							someKey: true,
// 							uid: 7,
// 							userContextKey: true,
// 						},
// 						domain: [["product_id", "=", 37]],
// 						name: "Partners",
// 						res_model: "partner",
// 						target: "current",
// 						type: "ir.actions.act_window",
// 						view_mode: "list",
// 						views: [
// 							[false, "list"],
// 							[2, "form"],
// 						],
// 					},
// 				);
// 				return Promise.resolve(true);
// 			},
// 		};
//     });
	
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

test(
	"columns are highlighted when hovering an origin (comparison mode)",
	async () => {
		expect.assertions(5);

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

		// hover the second origin in second group
		await contains("th.o_pivot_origin_row:nth-of-type(5)").hover();
		expect(".o_cell_hover").toHaveCount(3);
		for (let i = 1; i <= 3; i++) {
			expect(`tbody tr:nth-of-type(${i}) td:nth-of-type(5)`).toHaveClass("o_cell_hover");
		}
		await contains(".o_pivot_buttons button.dropdown-toggle").hover();
		expect(".o_cell_hover").toHaveCount(0);

	}
);

test('pivot view with disable_linking="True"', async () => {
	mockService("action", () => {
		return {
			doAction() {
				throw new Error("should not execute an action");
			},
		};
    });

	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot disable_linking="True">
				<field name="foo" type="measure"/>
			</pivot>`,
	});

	expect("table").not.toHaveClass("o_enable_linking");
	expect(".o_pivot_cell_value").toHaveCount(1);
	await contains(".o_pivot_cell_value").click(); // should not trigger a do_action
});

test('clicking on the "Total" cell with time range activated', async () => {
	expect.assertions(2);

	patchDate("2016-12-20T1:00:00");

	mockService("action", () => {
		return {
			doAction(action) {
				expect(action.domain).toEqual(
					["&", ["date", ">=", "2016-12-01"], ["date", "<=", "2016-12-31"]],
				);
				return Promise.resolve(true);
			},
		};
    });

	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: "<pivot/>",
		searchViewArch: `
			<search>
				<filter name="date_filter" date="date" domain="[]" default_period='this_month'/>
			</search>`,
		context: { search_default_date_filter: true },
	});

	expect("table").toHaveClass("o_enable_linking");
	await contains(".o_pivot_cell_value").click();
});

test(
	'clicking on a fake cell value ("empty group") in comparison mode',
	async () => {
		expect.assertions(3);

		patchDate("2016-12-20T1:00:00");
		Partner._records[0].date = "2016-11-15";
		Partner._records[1].date = "2016-12-17";
		Partner._records[2].date = "2016-11-22";
		Partner._records[3].date = "2016-11-03";
		
		const expectedDomains = [
			["&", ["date", ">=", "2016-12-01"], ["date", "<=", "2016-12-31"]],
			[[0, "=", 1]],
		];
		mockService("action", () => {
			return {
				doAction(action) {
					expect(action.domain).toEqual(expectedDomains.shift());
					return Promise.resolve(true);
				},
			};
		});

		await mountView({
			type: "pivot",
			resModel: "partner",
			arch: `<pivot><field name="product_id" type="row"/></pivot>`,
			searchViewArch: `
				<search>
					<filter name="date_filter" date="date" domain="[]" default_period='this_month'/>
				</search>`,
			context: { search_default_date_filter: true },
		});

		await toggleSearchBarMenu();
		await toggleMenuItem("Date: Previous period");

		expect("table").toHaveClass("o_enable_linking");
		// here we click on the group corresponding to Total/Total/This Month
		await contains(".o_pivot_cell_value:eq(1)").click(); // should trigger a do_action with appropriate domain
		// here we click on the group corresponding to xphone/Total/This Month
		await contains(".o_pivot_cell_value:eq(4)").click(); // should trigger a do_action with appropriate domain
	}
);

test("pivot view grouped by date field", async () => {
	expect.assertions(2);

	onRpc(({ method, kwargs }) => {
		if(method === "read_group") {
			const wrongFields = kwargs.fields.filter((field) => {
				return !(field.split(":")[0] in Partner._fields);
			});
			expect(wrongFields.length).toBe(0);
		}
	});

	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot>
				<field name="date" interval="month" type="col"/>
				<field name="foo" type="measure"/>
			</pivot>`,
	});
});

test("without measures, pivot view uses __count by default", async () => {
	Partner._fields.computed_field = fields.Integer({ string: "Computed and not stored", compute: false, aggregator: null });
	Partner._fields.foo = fields.Integer({ string: "Foo", searchable: true, aggregator: null });
	expect.assertions(4);

	onRpc(({method, kwargs}) => {
		if (method === "read_group") {
			expect(kwargs.fields).toEqual(["__count"]);
		}
	});

	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: "<pivot></pivot>",
	});

	await contains(".o_pivot_buttons .dropdown-toggle").click();
	const dropdownMenu = getDropdownMenu(".o_pivot_buttons button.dropdown-toggle");
	expect(queryAll(".dropdown-item", {root: dropdownMenu})).toHaveCount(1);
	const measure = dropdownMenu.querySelector(".dropdown-item");
	expect(measure).toHaveText("Count");
	expect(measure).toHaveClass("selected");
});

test("pivot view grouped by many2one field", async () => {
	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot>
				<field name="product_id" type="row"/>
				<field name="foo" type="measure"/>
			</pivot>`,
	});

	expect(".o_pivot_header_cell_opened").toHaveCount(1);
	expect(".o_pivot_header_cell_closed:contains(xphone)").toHaveCount(1);
	expect(".o_pivot_header_cell_closed:contains(xpad)").toHaveCount(1);
});

test("pivot view can be reloaded", async () => {
	let readGroupCount = 0;
	onRpc(({ method }) => {
		if (method === "read_group") {
			readGroupCount++;
		}
	})
	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: "<pivot></pivot>",
		searchViewArch: `
			<search>
				<filter name="some_filter" string="Some Filter" domain="[('foo', '>', 10)]"/>
			</search>`,
	});
	expect("td.o_pivot_cell_value:contains(4)").toHaveCount(1);
	expect(readGroupCount).toBe(1);
	await toggleSearchBarMenu();
	await toggleMenuItem("Some Filter");
	expect("td.o_pivot_cell_value:contains(2)").toHaveCount(1);
	expect(readGroupCount).toBe(2);
});

test("basic folding/unfolding", async () => {
	expect.assertions(7);
	Partner._fields.create_date = fields.Datetime({
		groupable: false,
        string: "Created on",
    });
    Partner._fields.write_date = fields.Datetime({
        string: "Last Modified on",
		groupable: false,
    });
	let rpcCount = 0;

	onRpc(({method}) => {
		if (method === "read_group") {
			rpcCount++;
		}
	});

	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot>
				<field name="product_id" type="row"/>
				<field name="foo" type="measure"/>
			</pivot>`,
	});

	expect("tbody tr").toHaveCount(3);
	// click on the opened header to close it
	await contains(".o_pivot_header_cell_opened").click();
	expect("tbody tr").toHaveCount(1);
	// click on closed header to open dropdown
	await contains("tbody .o_pivot_header_cell_closed").click();
	expect(".o-dropdown--menu").toHaveCount(1);
	expect(queryText(".o-dropdown--menu").replace(/\s/g, ""))
		.toBe("CompanyTypeCustomerDateOtherProductProductbarAddCustomGroupCompanyTypeCustomerDateOtherProductProductbar");
	// open the Date sub dropdown
	await contains(".o-dropdown--menu .dropdown-toggle.o_menu_item").hover();
	const subDropdownMenu = getDropdownMenu(".o-dropdown--menu .dropdown-toggle.o_menu_item");
	expect(subDropdownMenu.innerText.replace(/\s/g, "")).toEqual("YearQuarterMonthWeekDay");

	await contains(queryOne(".dropdown-item:eq(2)", {root: subDropdownMenu})).click();
	expect("tbody tr").toHaveCount(4);
	expect(rpcCount).toBe(3);
});

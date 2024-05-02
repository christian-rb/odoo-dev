/** @odoo-module */

import { expect, test } from "@odoo/hoot";
import { queryAll, queryAllTexts, queryOne, queryText } from "@odoo/hoot-dom";
import { Deferred, animationFrame } from "@odoo/hoot-mock";
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
	toggleMenuItemOption,
	toggleSaveFavorite,
	editFavoriteName,
	saveFavorite,
} from "@web/../tests/web_test_helpers";

function getCurrentValues() {
	return queryAllTexts(".o_pivot_cell_value div").join();
}

async function removeFacet() {
	await contains("div.o_searchview_facet:eq(0) .o_facet_remove").click();
}

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

	create_date = fields.Datetime({
		groupable: false,
		string: "Created on",
	});
	write_date = fields.Datetime({
		string: "Last Modified on",
		groupable: false,
	});

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

// test("clicking on a cell triggers a doAction", async () => {
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

test("more folding/unfolding", async () => {
	expect.assertions(1);

	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot>
				<field name="product_id" type="row"/>
				<field name="foo" type="measure"/>
			</pivot>`,
	});

	// open dropdown to zoom into first row
	await contains("tbody .o_pivot_header_cell_closed").click();
	// click on date by day
	await contains(".o-dropdown--menu .dropdown-toggle").hover();
	const subDropdownMenu = getDropdownMenu(".o-dropdown--menu .dropdown-toggle");
	await contains(queryOne("span:nth-child(5)", { root: subDropdownMenu })).click();

	// open dropdown to zoom into second row
	await contains("tbody th.o_pivot_header_cell_closed:eq(1)").click();
	expect("tbody tr").toHaveCount(7);
});

test("fold and unfold header group", async () => {
	expect.assertions(3);
	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot>
				<field name="product_id" type="col"/>
				<field name="foo" type="measure"/>
			</pivot>`,
	});


	expect("thead tr").toHaveCount(3);

	// fold opened col group
	await contains("thead .o_pivot_header_cell_opened").click();
	expect("thead tr").toHaveCount(2);

	// unfold it
	await contains("thead .o_pivot_header_cell_closed").click();
	await contains(".o-dropdown--menu span:nth-child(5)").click();
	expect("thead tr").toHaveCount(3);
});

test("unfold second header group", async () => {
	expect.assertions(4);

	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot>
				<field name="product_id" type="col"/>
				<field name="foo" type="measure"/>
			</pivot>`,
	});

	expect("thead tr").toHaveCount(3);
	let values = ["12", "20", "32"];
	expect(getCurrentValues()).toBe(values.join(","));

	// unfold it
	await contains("thead .o_pivot_header_cell_closed:last-child").click();
	await contains(".o-dropdown--menu span:nth-child(1)").click();
	expect("thead tr").toHaveCount(4);
	values = ["12", "17", "3", "32"];
	expect(getCurrentValues()).toBe(values.join(","));
});

test(
	"pivot renders group dropdown same as search groupby dropdown if group bys are specified in search arch",
	async () => {
		expect.assertions(6);

		await mountView({
			type: "pivot",
			resModel: "partner",
			arch: `
			<pivot>
				<field name="product_id" type="row"/>
				<field name="bar" type="col"/>
				<field name="foo" type="measure"/>
			</pivot>`,
			// TOASK DAM: <search><field/></search> won´t appear in groupbymenu ?
			searchViewArch: `
			<search>
				<filter name="bar" string="bar" context="{'group_by': 'bar'}"/>
				<filter name="foo" string="foo" context="{'group_by': 'foo'}"/>
				<filter name="product_id" string="product" context="{'group_by': 'product_id'}"/>
			</search>`,
		});

		// open group by dropdown
		await toggleSearchBarMenu();
		expect(".o-dropdown--menu .o_menu_item").toHaveCount(6);
		expect(".o-dropdown--menu .o_add_custom_group_menu").toHaveCount(1);
		// click on closed header to open dropdown
		await contains("tbody tr:last-child .o_pivot_header_cell_closed").click();
		expect(".dropdown-menu > .dropdown-item").toHaveCount(4);
		expect(".o-dropdown--menu .o_add_custom_group_menu").toHaveCount(1);
		// check custom groupby selection has groupable fields only
		expect(".o_add_custom_group_menu option:not([disabled])").toHaveCount(6);
		const optionDescriptions = queryAllTexts(".o_add_custom_group_menu option:not([disabled])");
		expect(optionDescriptions).toEqual(
			["Company Type", "Customer", "Date", "Other Product", "Product", "bar"],
		);
	}
);

test("pivot group dropdown sync with search groupby dropdown", async () => {
	
	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot>
				<field name="product_id" type="row"/>
				<field name="foo" type="measure"/>
			</pivot>`,
		searchViewArch: `
			<search>
				<filter name="bar" string="bar" context="{'group_by': 'bar'}"/>
				<filter name="product_id" string="product" context="{'group_by': 'product_id'}"/>
			</search>`,
	});

	// open group by dropdown
	await toggleSearchBarMenu()
	expect(".o-dropdown--menu .o_menu_item").toHaveCount(5);
	// click on closed header to open dropdown
	await contains("tbody tr:last-child .o_pivot_header_cell_closed").click();
	expect(".o-dropdown--menu .o_menu_item").toHaveCount(3);
	// add a custom group in searchview groupby
	await toggleSearchBarMenu();
	await contains(`.o_add_custom_group_menu`).select("company_type");
	expect(".o-dropdown--menu .o_menu_item").toHaveCount(6);
	await contains("tbody tr:last-child .o_pivot_header_cell_closed").click();
	expect(".o-dropdown--menu .o_menu_item").toHaveCount(3);
	// add a custom group in pivot groupby
	await contains(`.o_add_custom_group_menu`).select("date");
	// click on closed header to open groupby selection dropdown
	await contains("tbody tr:last-child .o_pivot_header_cell_closed").click();
	expect(".o-dropdown--menu .o_menu_item").toHaveCount(4);
	// applying custom groupby in pivot groupby dropdown will not update search dropdown
	await toggleSearchBarMenu();
	expect(".o-dropdown--menu .o_menu_item").toHaveCount(6);
});

test(
	"pivot custom groupby: grouping on date field use default interval month",
	async () => {
		expect.assertions(1);

		let checkReadGroup = false;
		onRpc(({ method, kwargs }) => {
			if (method === "read_group" && checkReadGroup) {
				expect(kwargs.groupby).toEqual(["date:month"]);
				checkReadGroup = false;
			}
		})

		await mountView({
			type: "pivot",
			resModel: "partner",
			arch: `
				<pivot>
					<field name="product_id" type="row"/>
					<field name="foo" type="measure"/>
				</pivot>`,
			searchViewArch: `
				<search>
					<filter name="bar" string="bar" context="{'group_by': 'bar'}"/>
				</search>`,
		});

		// click on closed header to open dropdown and apply groupby on date field
		await contains("thead .o_pivot_header_cell_closed").click();
		checkReadGroup = true;
		await contains(`.o_add_custom_group_menu`).select("date");
	}
);

test(
	"pivot groupby dropdown renders custom search at the end with separator",
	async () => {
		await mountView({
			type: "pivot",
			resModel: "partner",
			arch: `
				<pivot>
					<field name="product_id" type="row"/>
					<field name="foo" type="measure"/>
				</pivot>`,
			searchViewArch: `
				<search>
					<filter name="bar" string="bar" context="{'group_by': 'bar'}"/>
					<filter name="product_id" string="product" context="{'group_by': 'product_id'}"/>
				</search>`,
		});

		// open group by dropdown
		await toggleSearchBarMenu();
		expect(".o-dropdown--menu .o_menu_item").toHaveCount(5);
		await contains(`.o_add_custom_group_menu`).select("company_type");
		expect(".o-dropdown--menu .o_menu_item").toHaveCount(6);
		// click on closed header to open dropdown
		await contains("tbody .o_pivot_header_cell_closed:eq(1)").click();
		let items = queryAll(".o_menu_item:not(select)");
		expect(queryAllTexts(items)).toEqual(["bar", "product"]);
		expect(".o-dropdown--menu .dropdown-divider").toHaveCount(1);
		expect(items[items.length - 1].nextElementSibling).toHaveClass("dropdown-divider");
		// add a custom group in pivot groupby
		await contains(`.o_add_custom_group_menu`).select("customer");
		await contains("tbody .o_pivot_header_cell_closed:eq(1)").click();
		items = queryAll(".o_menu_item:not(select)");
		expect(queryAllTexts(items)).toEqual(["bar", "product", "Customer"]);
		expect(".o-dropdown--menu .dropdown-divider").toHaveCount(2);
		expect(items[items.length - 1].previousElementSibling).toHaveClass("dropdown-divider");
		expect(items[items.length - 1].nextElementSibling).toHaveClass("dropdown-divider");
	}
);

test("pivot view without group by specified in search arch", async () => {
	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot>
				<field name="product_id" type="row"/>
				<field name="foo" type="measure"/>
			</pivot>`,
	});

	// open group by dropdown
	await toggleSearchBarMenu();
	expect(".o-dropdown--menu .o_menu_item").toHaveCount(3);
	expect(".o-dropdown--menu .o_add_custom_group_menu").toHaveCount(1);
	// click on closed header to open dropdown
	await contains("tbody .o_pivot_header_cell_closed:eq(1)").click();
	expect(".o-dropdown--menu .o_menu_item").toHaveCount(7);
	expect(".o-dropdown--menu .o_add_custom_group_menu").toHaveCount(1);
});

test(
	"pivot view do not show custom group selection if there are no groupable fields",
	async () => {
		expect.assertions(4);

		for (const fieldName of [
			"bar",
			"company_type",
			"customer",
			"date",
			"other_product_id",
		]) {
			delete Partner._fields[fieldName];
		}

		// Keep product_id but make it ungroupable
		Partner._fields.product_id = fields.Many2one({ string: "Product", relation: "product", store: true, sortable: true, groupable: false});

		Partner._records = [
			{
				id: 1,
				foo: 12,
				product_id: 37,
				computed_field: 19,
			},
		];

		await mountView({
			type: "pivot",
			resModel: "partner",
			arch: `
				<pivot>
					<field name="foo" type="measure"/>
					<field name="product_id" invisible="1"/>
				</pivot>`,
			searchViewArch: `
				<search>
					<filter name="product_id" string="product" context="{'group_by': 'product_id'}"/>
				</search>`,
		});

		// open group by dropdown
		await toggleSearchBarMenu();
		expect(".o-dropdown--menu .dropdown-item").toHaveCount(3);
		expect(".o-dropdown--menu .o_add_custom_group_menu").toHaveCount(0);

		// click on closed header to open dropdown
		await contains("tbody .o_pivot_header_cell_closed").click();
		expect(".o-dropdown--menu .dropdown-item").toHaveCount(1);
		expect(".o-dropdown--menu .o_add_custom_group_menu").toHaveCount(0);
	}
);

test("can toggle extra measure", async () => {
	let rpcCount = 0;
	onRpc(() => {
		rpcCount++;
	})
	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot>
				<field name="product_id" type="row"/>
				<field name="foo" type="measure"/>
			</pivot>`,
	});

	rpcCount = 0;
	expect(".o_pivot_cell_value").toHaveCount(3);
	await contains(".o_pivot_buttons button.dropdown-toggle").click();
	expect(".dropdown-item:contains(Count)").not.toHaveClass("selected");
	await contains(".dropdown-item:contains(Count):eq(0").click();
	expect(".dropdown-item:contains(Count)").toHaveClass("selected");
	expect(".o_pivot_cell_value").toHaveCount(6);
	expect(rpcCount).toBe(2);
	await contains(".dropdown-item:contains(Count):eq(0)").click();
	expect(".dropdown-item:contains(Count):eq(0)").not.toHaveClass("selected");
	expect(".o_pivot_cell_value").toHaveCount(3);
	expect(rpcCount).toBe(2);
});

test("no content helper when no active measure", async () => {
	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `<pivot/>`,
	});

	expect(".o_view_nocontent").toHaveCount(0);
	expect("table").toHaveCount(1);

	await contains(".o_pivot_buttons button.dropdown-toggle").click();
	await contains(".dropdown-item:contains(Count):eq(0)").click();

	expect(".o_view_nocontent").toHaveCount(1);
	expect("table").toHaveCount(0);
});

test("no content helper when no data", async () => {
	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `<pivot/>`,
		searchViewArch: `
			<search>
				<filter name="some_filter" string="Some Filter" domain="[('foo', '=', 12345)]"/>
			</search>`,
	});

	expect(".o_view_nocontent").toHaveCount(0);
	expect("table").toHaveCount(1);

	await toggleSearchBarMenu();
	await toggleMenuItem("Some Filter");

	expect(".o_view_nocontent").toHaveCount(1);
	expect("table").toHaveCount(0);
});

test("no content helper when no data, part 2", async () => {
	Partner._records = [];

	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: "<pivot/>",
	});

	expect(".o_view_nocontent").toHaveCount(1);
});

test("no content helper when no data, part 3", async () => {
	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: "<pivot/>",
		searchViewArch: `
			<search>
				<field name="foo"/>
				<filter name="some_filter" string="Some Filter" domain="[('foo', '>', 10)]"/>
			</search>`,
		context: {
			search_default_foo: 12345,
		},
	});

	expect(".o_searchview .o_searchview_facet").toHaveCount(1);
	expect(".o_view_nocontent").toHaveCount(1);

	await toggleSearchBarMenu();
	await toggleMenuItem("Some Filter");
	expect(".o_searchview .o_searchview_facet").toHaveCount(2)
	expect(".o_view_nocontent").toHaveCount(1);

	await toggleMenuItem("Some Filter");
	expect(".o_searchview .o_searchview_facet").toHaveCount(1);
	expect(".o_view_nocontent").toHaveCount(1);

	await contains(".o_facet_remove").click();
	expect(".o_searchview .o_searchview_facet").toHaveCount(0);
	expect(".o_view_nocontent").toHaveCount(0);

	// tries to open a field selection menu, to make sure it was not
	// removed from the dom.
	await contains("tbody .o_pivot_header_cell_closed").click();
	expect(".o-dropdown--menu").toHaveCount(1);
});

test("tries to restore previous state after domain change", async () => {
	expect.assertions(7);
	let rpcCount = 0;
	onRpc(() => {
		rpcCount++;
	})
	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot>
				<field name="product_id" type="row"/>
				<field name="foo" type="measure"/>
			</pivot>`,
		searchViewArch: `
			<search>
				<filter name="my_filter" string="My Filter" domain="[('foo', '=', 12345)]"/>
			</search>`,
	});

	expect(".o_pivot_cell_value").toHaveCount(3);
	expect(".o_pivot_measure_row:contains(Foo)").toHaveCount(1);

	await toggleSearchBarMenu();
	await toggleMenuItem("My Filter");
	expect("table").toHaveCount(0);

	rpcCount = 0;
	await removeFacet();

	expect("table").toHaveCount(1);
	expect(rpcCount).toBe(2);
	expect(".o_pivot_cell_value").toHaveCount(3);
	expect(".o_pivot_measure_row:contains(Foo)").toHaveCount(1);
});

test("can be grouped with the search view", async () => {
	expect.assertions(4);

	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot>
				<field name="foo" type="measure"/>
			</pivot>`,
		searchViewArch: `
			<search>
				<filter string="Product" name="product_id" context="{'group_by':'product_id'}"/>
			</search>`,
	});

	expect(".o_pivot_cell_value", "should have only 1 cell").toHaveCount(1);
	expect("tbody tr", "should have 1 rows").toHaveCount(1);

	await toggleSearchBarMenu();
	await toggleMenuItem("Product");

	expect(".o_pivot_cell_value").toHaveCount(3);
	expect("tbody tr").toHaveCount(3);
});

test("can sort data in a column by clicking on header", async () => {
	expect.assertions(3);

	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot>
				<field name="foo" type="measure"/>
				<field name="product_id" type="row"/>
			</pivot>`,
	});

	let values = ["32", "12", "20"];
	expect(getCurrentValues()).toEqual(values.join(","));

	await contains("th.o_pivot_measure_row").click();

	values = ["32", "12", "20"];
	expect(getCurrentValues()).toEqual(values.join(","));

	await contains("th.o_pivot_measure_row").click();

	values = ["32", "20", "12"];
	expect(getCurrentValues()).toEqual(values.join(","));
});

test("can expand all rows", async () => {
	expect.assertions(7);

	let nbReadGroups = 0;
	onRpc(({method}) => {
		if (method === "read_group") {
			nbReadGroups++;
		}
	});
	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot>
				<field name="foo" type="measure"/>
				<field name="product_id" type="row"/>
			</pivot>`,
		searchViewArch: `
			<search>
				<filter string="Date" name="date" context="{'group_by':'date'}"/>
				<filter string="Product" name="product_id" context="{'group_by':'product_id'}"/>
			</search>`,
	});

	expect(nbReadGroups).toEqual(2);
	expect(getCurrentValues()).toBe("32,12,20");

	// expand on date:days, product
	await toggleSearchBarMenu();
	await toggleMenuItem("Date");
	await toggleMenuItemOption("Date", "Month");
	nbReadGroups = 0;
	await toggleMenuItem("Product");

	expect(nbReadGroups).toEqual(3);
	expect("tbody tr").toHaveCount(8);

	// collapse the first two rows
	await contains("tbody .o_pivot_header_cell_opened:eq(2)").click();
	await contains("tbody .o_pivot_header_cell_opened:eq(1)").click();

	expect("tbody tr").toHaveCount(6);

	// expand all
	nbReadGroups = 0;
	await contains(".o_pivot_expand_button").click();

	expect(nbReadGroups).toEqual(3);
	expect("tbody tr").toHaveCount(8);
});

test("expand all with a delay", async () => {
	expect.assertions(4);

	let def;
	onRpc(({method}) => {
		if (method === "read_group") {
			return Promise.resolve(def);
		}
	});
	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot>
				<field name="foo" type="measure"/>
				<field name="product_id" type="row"/>
			</pivot>`,
		searchViewArch: `
			<search>
				<filter string="Date" name="date" context="{'group_by':'date'}"/>
				<filter string="Product" name="product_id" context="{'group_by':'product_id'}"/>
			</search>`,
	});

	// expand on date:days, product
	await toggleSearchBarMenu();
	await toggleMenuItem("Date");
	await toggleMenuItemOption("Date", "Month");
	await toggleMenuItem("Product");
	expect("tbody tr").toHaveCount(8);

	// collapse the first two rows
	await contains("tbody .o_pivot_header_cell_opened:eq(2)").click();
	await contains("tbody .o_pivot_header_cell_opened:eq(1)").click();

	expect("tbody tr").toHaveCount(6);

	// expand all
	def = new Deferred();
	await contains(".o_pivot_expand_button").click();
	expect("tbody tr").toHaveCount(6);
	def.resolve();
	await animationFrame();
	expect("tbody tr").toHaveCount(8);
});

// test.debug("can download a file", async () => {
// 	expect.assertions(1);

// 	mockDownload(({ url }) => {
// 		expect(url).toBe("/web/pivot/export_xlsx");
// 		return Promise.resolve();
// 	});

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
// 		arch: `
// 			<pivot>
// 				<field name="date" interval="month" type="col"/>
// 				<field name="foo" type="measure"/>
// 			</pivot>`,
// 	});

// 	await contains(".o_pivot_download").click();
// });

// test(
// 	"download a file with single measure, measure row displayed in table",
// 	async function (assert) {
// 		expect.assertions(2);

// 		mockDownload(({ url, data }) => {
// 			data = JSON.parse(data.data);
// 			expect(url).toBe("/web/pivot/export_xlsx");
// 			expect(data.measure_headers.length).toBe(4);
// 			return Promise.resolve();
// 		});

// 		await mountView({
// 			type: "pivot",
// 			resModel: "partner",
			
// 			arch: `
// 				<pivot>
// 					<field name="date" interval="month" type="col"/>
// 					<field name="foo" type="measure"/>
// 				</pivot>`,
// 		});

// 		await contains(".o_pivot_download").click();
// 	}
// );

// test("download button is disabled when there is no data", async () => {
// 	expect.assertions(1);

// 	Partner._records =[];

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
// 		arch: `
// 			<pivot>
// 				<field name="date" interval="month" type="col"/>
// 				<field name="foo" type="measure"/>
// 			</pivot>`,
// 	});

// 	assert.ok(
// 		target.querySelector(".o_pivot_download").disabled,
// 		"download button should be disabled"
// 	);
// });

test("correctly save measures and groupbys to favorite", async () => {
	expect.assertions(3);

	let expectedContext;
	onRpc(({ method, args }) => {
		if (method === "create_or_replace") {
			expect(args[0].context).toEqual(expectedContext);
			return true;
		}
	});
	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot>
				<field name="date" interval="day" type="col"/>
				<field name="foo" type="measure"/>
			</pivot>`,
	});

	expectedContext = {
		group_by: [],
		pivot_column_groupby: ["date:day"],
		pivot_measures: ["foo"],
		pivot_row_groupby: [],
	};
	await toggleSearchBarMenu();
	await toggleSaveFavorite();
	await editFavoriteName("Fav1");
	await saveFavorite();

	// expand header on field customer
	await contains("thead .o_pivot_header_cell_closed:eq(1)").click();
	await contains(".o-dropdown--menu .dropdown-item:eq(1)").click();
	expectedContext = {
		group_by: [],
		pivot_column_groupby: ["date:day", "customer"],
		pivot_measures: ["foo"],
		pivot_row_groupby: [],
	};
	await toggleSearchBarMenu();
	await toggleSaveFavorite();
	await editFavoriteName("Fav2");
	await saveFavorite();

	// expand row on field product_id
	await contains("tbody .o_pivot_header_cell_closed").click();
	await contains(".o-dropdown--menu .dropdown-item:eq(4)").click();
	expectedContext = {
		group_by: [],
		pivot_column_groupby: ["date:day", "customer"],
		pivot_measures: ["foo"],
		pivot_row_groupby: ["product_id"],
	};
	await toggleSearchBarMenu();
	await toggleSaveFavorite();
	await editFavoriteName("Fav3");
	await saveFavorite();
});

test("correctly remove pivot_ keys from the context", async () => {
	expect.assertions(5);

	// in this test, we use "foo" as a measure
	Partner._fields.foo = fields.Integer({ string: "Foo", searchable: true, aggregator: "sum", groupable: false, store: true });
	Partner._fields.amount = fields.Float({
        string: "Amount",
		aggregator: "sum"
    });

	let expectedContext;

	onRpc(({method, args}) => {
		if (method === "create_or_replace") {
			expect(args[0].context).toEqual(expectedContext);
			return true;
		}
	});

	await mountView({
		type: "pivot",
		resModel: "partner",
		arch: `
			<pivot>
				<field name="date" interval="day" type="col"/>
				<field name="amount" type="measure"/>
			</pivot>`,
		context: {
			search_default_initial_context: 1,
		},
		searchViewArch: `
			<search>
				<filter
					name="initial_context"
					string="Initial favorite"
					domain="[]"
					context="{
						'pivot_measures': ['foo'],
						'pivot_column_groupby': ['customer'],
						'pivot_row_groupby': ['product_id'],
					}"
				/>
			</search>`,
	});

	// Unload the filter
	await removeFacet(); // remove previous favorite
	expectedContext = {
		group_by: [],
		pivot_column_groupby: ["customer"],
		pivot_measures: ["foo"],
		pivot_row_groupby: ["product_id"],
	};
	await toggleSearchBarMenu();
	await toggleSaveFavorite();
	await editFavoriteName("1");
	await saveFavorite();

	// Let's get rid of the rows groupBy
	await contains("tbody .o_pivot_header_cell_opened").click();
	expectedContext = {
		group_by: [],
		pivot_column_groupby: ["customer"],
		pivot_measures: ["foo"],
		pivot_row_groupby: [],
	};
	await toggleSearchBarMenu();
	await toggleSaveFavorite();
	await editFavoriteName("2");
	await saveFavorite();

	// And now, get rid of both col and row groupby
	//await contains("tbody .o_pivot_header_cell_opened").click(); //It was already removed
	await contains("thead .o_pivot_header_cell_opened").click();
	expectedContext = {
		group_by: [],
		pivot_column_groupby: [],
		pivot_measures: ["foo"],
		pivot_row_groupby: [],
	};
	await toggleSearchBarMenu();
	await toggleSaveFavorite();
	await editFavoriteName("3");
	await saveFavorite();

	// Group row by product_id
	await contains("tbody .o_pivot_header_cell_closed").click();
	await contains(".o-dropdown--menu span:nth-child(5)").click();
	expectedContext = {
		group_by: [],
		pivot_column_groupby: [],
		pivot_measures: ["foo"],
		pivot_row_groupby: ["product_id"],
	};
	await toggleSearchBarMenu();
	await toggleSaveFavorite();
	await editFavoriteName("4");
	await saveFavorite();

	// Group column by customer
	await contains("thead .o_pivot_header_cell_closed").click();
	await contains(".o-dropdown--menu span:nth-child(2)").click();
	expectedContext = {
		group_by: [],
		pivot_column_groupby: ["customer"],
		pivot_measures: ["foo"],
		pivot_row_groupby: ["product_id"],
	};
	await toggleSearchBarMenu();
	await toggleSaveFavorite();
	await editFavoriteName("5");
	await saveFavorite();
});

test.debug("Apply two groupby, and remove facet", async () => {
	serverData.views = {
		"partner,false,pivot": `
				<pivot>
					<field name="customer" type="row"/>
				</pivot>`,
		"partner,false,search": `
				<search>
					<filter name="group_by_product" string="Product" domain="[]" context="{'group_by': 'product_id'}"/>
					<filter name="group_by_bar" string="Bar" domain="[]" context="{'group_by': 'bar'}"/>
				</search>`,
	};

	const webClient = await createWebClient({ serverData });

	await doAction(webClient, {
		res_model: "partner",
		type: "ir.actions.act_window",
		views: [[false, "pivot"]],
	});

	expect("tbody .o_pivot_header_cell_closed").toHaveText("First");

	// Apply both groupbys
	await toggleSearchBarMenu();
	await toggleMenuItem("Product");
	expect("tbody .o_pivot_header_cell_closed").toHaveText("xphone");

	await toggleMenuItem("Bar");
	expect("tbody .o_pivot_header_cell_closed").toHaveText("Yes");

	// remove filter
	await removeFacet();

	expect("tbody .o_pivot_header_cell_closed").toHaveText("Yes");
});

// test("Add a group by on the CP when a favorite already exists", async () => {
// 	serverData.views = {
// 		"partner,false,pivot": `
// 				<pivot>
// 				</pivot>`,
// 		"partner,false,search": `
// 				<search>
// 					<filter name="groubybar" string="Bar" domain="[]" context="{'group_by': 'bar'}"/>
// 				</search>`,
// 	};

// 	serverData.models.partner.filters = [
// 		{
// 			context: "{'pivot_row_groupby': ['date']}",
// 			domain: "[]",
// 			id: 7,
// 			is_default: true,
// 			name: "My favorite",
// 			sort: "[]",
// 			user_id: [2, "Mitchell Admin"],
// 		},
// 	];

// 	const webClient = await createWebClient({ serverData });

// 	await doAction(webClient, {
// 		res_model: "partner",
// 		type: "ir.actions.act_window",
// 		views: [[false, "pivot"]],
// 	});

// 	expect(queryText("tbody .o_pivot_header_cell_closed")).toBe("April 2016");

// 	// Apply BAR groupbys
// 	await toggleSearchBarMenu();
// 	await toggleMenuItem("Bar");
// 	expect(queryText("tbody .o_pivot_header_cell_closed")).toBe("No");

// 	// remove groupBy
// 	await toggleMenuItem("Bar");
// 	expect(queryText("tbody .o_pivot_header_cell_closed")).toBe("April 2016");

// 	// remove all facets
// 	await removeFacet();

// 	expect(queryText("tbody .o_pivot_header_cell_closed")).toBe("April 2016");
// });

// QUnit.skip("Removing or adding filter shouldn't modify the row group", async () => {
// 	serverData.views = {
// 		"partner,false,pivot": `
// 				<pivot>
// 					<field name="customer" type="row"/>
// 				</pivot>`,
// 		"partner,false,search": `
// 				<search>
// 					<filter name="bayou" string="Bayou" domain="[('foo','=', 12)]"/>
// 				</search>`,
// 	};

// 	const webClient = await createWebClient({ serverData });

// 	await doAction(webClient, {
// 		res_model: "partner",
// 		type: "ir.actions.act_window",
// 		views: [[false, "pivot"]],
// 		context: { search_default_bayou: 1, group_by: ["company_type"] },
// 	});

// 	expect(queryText("tbody .o_pivot_header_cell_closed")).toBe("Company");

// 	// Let's get rid of the rows groupBy
// 	await contains("tbody .o_pivot_header_cell_opened").click();

// 	expect(queryText("tbody .o_pivot_header_cell_closed")).toBe("Total");

// 	// Group row by product_id
// 	await contains("tbody .o_pivot_header_cell_closed").click();
// 	await contains(".o-dropdown--menu span:nth-child(5)").click();

// 	expect(queryText("tbody .o_pivot_header_cell_closed")).toBe("xphone");

// 	// remove filter
// 	await removeFacet();

// 	expect(queryText("tbody .o_pivot_header_cell_closed")).toBe("xphone");
// });

// test(
// 	"Adding a Favorite at anytime should modify the row/column groupby",
// 	async function (assert) {
// 		serverData.views = {
// 			"partner,false,pivot": `
// 				<pivot>
// 					<field name="customer" type="row"/>
// 					<field name="date" interval="month" type="col" />
// 				</pivot>`,
// 			"partner,false,search": "<search/>",
// 		};
// 		serverData.models["partner"].filters = [
// 			{
// 				user_id: [2, "Mitchell Admin"],
// 				name: "My favorite",
// 				id: 5,
// 				context: `{"pivot_row_groupby":["product_id"], "pivot_column_groupby": ["bar"]}`,
// 				sort: "[]",
// 				domain: "",
// 				is_default: false,
// 				model_id: "partner",
// 				action_id: false,
// 			},
// 		];

// 		const webClient = await createWebClient({ serverData });

// 		await doAction(webClient, {
// 			res_model: "partner",
// 			type: "ir.actions.act_window",
// 			views: [[false, "pivot"]],
// 		});

// 		expect(queryText("tbody .o_pivot_header_cell_closed")).toBe("First");

// 		expect(queryText("thead .o_pivot_header_cell_closed")).toBe("April 2016");

// 		// activate the unique existing favorite
// 		await toggleSearchBarMenu();
// 		await toggleMenuItem(2);
// 		expect(queryText("tbody .o_pivot_header_cell_closed")).toBe("xphone");

// 		expect(queryText("thead .o_pivot_header_cell_closed")).toBe("No");

// 		// desactivate the unique existing favorite
// 		await toggleMenuItem(2);

// 		expect(queryText("tbody .o_pivot_header_cell_closed")).toBe("xphone");

// 		expect(queryText("thead .o_pivot_header_cell_closed")).toBe("No");

// 		// Let's get rid of the rows and columns groupBy
// 		await contains("tbody .o_pivot_header_cell_opened").click();
// 		await contains("thead .o_pivot_header_cell_opened").click();

// 		expect(queryText("tbody .o_pivot_header_cell_closed")).toBe("Total");

// 		expect(queryText("thead .o_pivot_header_cell_closed")).toBe("Total");

// 		// activate AGAIN the unique existing favorite
// 		await toggleSearchBarMenu();
// 		await toggleMenuItem(2);

// 		expect(queryText("tbody .o_pivot_header_cell_closed")).toBe("xphone");

// 		expect(queryText("thead .o_pivot_header_cell_closed")).toBe("No");
// 	}
// );

// test("Unload Filter, reset display, load another filter", async () => {
// 	expect.assertions(18);

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 			<pivot>
// 				<field name="foo" type="measure"/>
// 			</pivot>`,
// 		context: {
// 			pivot_measures: ["foo"],
// 			pivot_column_groupby: ["customer"],
// 			pivot_row_groupby: ["product_id"],
// 		},

// 		searchViewArch: `
// 			<search>
// 				<filter
// 					name="no_context_filter"
// 					string="My fake favorite"
// 					domain="[]"
// 					context="{}"
// 				/>
// 				<filter
// 					name="reset_filter"
// 					string="My fake favorite 2"
// 					domain="[]"
// 					context="{
// 						'pivot_measures': ['foo'],
// 						'pivot_column_groupby': ['customer'],
// 						'pivot_row_groupby': ['product_id'],
// 					}"
// 				/>
// 			</search>`,
// 	});

// 	// Check Columns
// 	expect($(target).find("thead .o_pivot_header_cell_opened").length).toBe(1);
// 	expect($(target).find('thead tr:contains("First")').length).toBe(1);
// 	expect($(target).find('thead tr:contains("Second")').length).toBe(1);

// 	// Check Rows
// 	expect($(target).find("tbody .o_pivot_header_cell_opened").length).toBe(1);
// 	expect($(target).find('tbody tr:contains("xphone")').length).toBe(1);
// 	expect($(target).find('tbody tr:contains("xpad")').length).toBe(1);

// 	// Equivalent to unload the filter
// 	await toggleSearchBarMenu();
// 	await toggleMenuItem("My fake favorite");
// 	// collapse all headers
// 	await contains(".o_pivot_header_cell_opened:first-child").click();
// 	await contains(".o_pivot_header_cell_opened").click();

// 	// Check Columns
// 	expect($(target).find("thead .o_pivot_header_cell_closed").length).toBe(1);
// 	expect($(target).find('thead tr:contains("First")').length).toBe(0);
// 	expect($(target).find('thead tr:contains("Second")').length).toBe(0);

// 	// Check Rows
// 	expect($(target).find("tbody .o_pivot_header_cell_closed").length).toBe(1);
// 	expect($(target).find('tbody tr:contains("xphone")').length).toBe(0);
// 	expect($(target).find('tbody tr:contains("xpad")').length).toBe(0);

// 	// Equivalent to load another filter
// 	await removeFacet(); // remove previously saved favorite
// 	await toggleSearchBarMenu();
// 	await toggleMenuItem("My fake favorite 2");

// 	// Check Columns
// 	expect($(target).find("thead .o_pivot_header_cell_opened").length).toBe(1);
// 	expect($(target).find('thead tr:contains("First")').length).toBe(1);
// 	expect($(target).find('thead tr:contains("Second")').length).toBe(1);

// 	// Check Rows
// 	expect($(target).find("tbody .o_pivot_header_cell_opened").length).toBe(1);
// 	expect($(target).find('tbody tr:contains("xphone")').length).toBe(1);
// 	expect($(target).find('tbody tr:contains("xpad")').length).toBe(1);
// });

// test("Reload, group by columns, reload", async () => {
// 	expect.assertions(2);

// 	let expectedContext;
// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: "<pivot/>",
// 		searchViewArch: `
// 			<search>
// 				<filter name="my_filter_1" string="My Filter 1" domain="[('product_id', '=', 37)]"/>
// 				<filter name="my_filter_2" string="My Filter 2" domain="[('product_id', '=', 41)]"/>
// 			</search>`,
// 		mockRPC(route, args) {
// 			if (args.method === "create_or_replace") {
// 				assert.deepEqual(args.args[0].context, expectedContext);
// 				return true;
// 			}
// 		},
// 	});

// 	// Set a column groupby
// 	await contains("thead .o_pivot_header_cell_closed").click();
// 	await contains(".o-dropdown--menu .dropdown-item:eq(1)").click();

// 	// Set a domain
// 	await toggleSearchBarMenu();
// 	await toggleMenuItem("My Filter 1");

// 	// Save to favorites and check that column groupbys were not lost
// 	expectedContext = {
// 		group_by: [],
// 		pivot_column_groupby: ["customer"],
// 		pivot_measures: ["__count"],
// 		pivot_row_groupby: [],
// 	};
// 	await toggleSaveFavorite(target);
// 	await editFavoriteName(target, "My favorite 1");
// 	await saveFavorite(target);

// 	// Set a column groupby
// 	await removeFacet(); // remove previously saved favorite
// 	await contains("thead .o_pivot_header_cell_closed").click();
// 	await contains(".o-dropdown--menu .dropdown-item:eq(4)").click();

// 	// Set a domain
// 	await toggleSearchBarMenu();
// 	await toggleMenuItem("My Filter 2");

// 	expectedContext = {
// 		group_by: [],
// 		pivot_column_groupby: ["customer", "product_id"],
// 		pivot_measures: ["__count"],
// 		pivot_row_groupby: [],
// 	};
// 	await toggleSaveFavorite(target);
// 	await editFavoriteName(target, "My favorite 2");
// 	await saveFavorite(target);
// });

// test("folded groups remain folded at reload", async () => {
// 	expect.assertions(5);

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 			<pivot>
// 				<field name="product_id" type="row"/>
// 				<field name="company_type" type="col"/>
// 				<field name="foo" type="measure"/>
// 			</pivot>`,
// 		searchViewArch: `
// 			<search>
// 				<filter name="dummy_filter" string="Dummy Filter" domain="[('id', '>', 0)]"/>
// 			</search>`,
// 	});

// 	let values = ["29", "3", "32", "12", "12", "17", "3", "20"];
// 	expect(getCurrentValues()).toBe(values.join(","));

// 	// expand a col group
// 	await contains("thead .o_pivot_header_cell_closed:eq(1)").click();
// 	await contains(".o-dropdown--menu .dropdown-item:eq(1)").click();

// 	values = ["29", "2", "1", "32", "12", "12", "17", "2", "1", "20"];
// 	expect(getCurrentValues()).toBe(values.join(","));

// 	// expand a row group
// 	await contains("tbody .o_pivot_header_cell_closed:eq(1)").click();
// 	await contains(".o-dropdown--menu .dropdown-item:eq(3)").click();

// 	values = ["29", "2", "1", "32", "12", "12", "17", "2", "1", "20", "17", "2", "1", "20"];
// 	expect(getCurrentValues()).toBe(values.join(","));

// 	// reload (should keep folded groups folded as col/row groupbys didn't change)
// 	await toggleSearchBarMenu();
// 	await toggleMenuItem("Dummy Filter");

// 	expect(getCurrentValues()).toBe(values.join(","));

// 	await contains(".o_pivot_expand_button").click();

// 	// sanity check of what the table should look like if all groups are
// 	// expanded, to ensure that the former asserts are pertinent
// 	values = [
// 		"12",
// 		"17",
// 		"2",
// 		"1",
// 		"32",
// 		"12",
// 		"12",
// 		"12",
// 		"12",
// 		"17",
// 		"2",
// 		"1",
// 		"20",
// 		"17",
// 		"2",
// 		"1",
// 		"20",
// 	];
// 	expect(getCurrentValues()).toBe(values.join(","));
// });

// test("Empty results keep groupbys", async () => {
// 	expect.assertions(6);

// 	const expectedContext = {
// 		group_by: [],
// 		pivot_column_groupby: ["customer"],
// 		pivot_measures: ["__count"],
// 		pivot_row_groupby: [],
// 	};

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: "<pivot/>",
// 		searchViewArch: `
// 			<search>
// 				<filter name="my_filter_1" string="My Filter 1" domain="[('id', '=', 0)]"/>
// 				<filter name="my_filter_2" string="My Filter 2" domain="[('product_id', '=', 37)]"/>
// 			</search>`,
// 		mockRPC(route, args) {
// 			if (args.method === "create_or_replace") {
// 				assert.deepEqual(args.args[0].context, expectedContext);
// 				return true;
// 			}
// 		},
// 	});

// 	// Set a column groupby
// 	await contains("thead .o_pivot_header_cell_closed").click();
// 	await contains(".o-dropdown--menu .dropdown-item:eq(1)").click();

// 	expect("table").toHaveCount(1);

// 	// Set a domain for empty results
// 	await toggleSearchBarMenu();
// 	await toggleMenuItem("My Filter 1");
// 	expect("table").toHaveCount(0);

// 	await toggleSaveFavorite(target);
// 	await editFavoriteName(target, "My favorite 1");
// 	await saveFavorite(target);

// 	// Set a domain for not empty results
// 	await removeFacet(); // remove previously saved favorite
// 	expect("table").toHaveCount(1);

// 	await toggleSearchBarMenu();
// 	await toggleMenuItem("My Filter 2");
// 	expect("table").toHaveCount(1);

// 	await toggleSaveFavorite(target);
// 	await editFavoriteName(target, "My favorite 2");
// 	await saveFavorite(target);
// });

// test("correctly uses pivot_ keys from the context", async () => {
// 	expect.assertions(7);

// 	// in this test, we use "foo" as a measure
// 	serverData.models.partner.fields.foo.store = true;
// 	serverData.models.partner.fields.amount = {
// 		string: "Amount",
// 		type: "float",
// 		aggregator: "sum",
// 	};

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 			<pivot>
// 				<field name="date" interval="day" type="col"/>
// 				<field name="amount" type="measure"/>
// 			</pivot>`,
// 		context: {
// 			pivot_measures: ["foo"],
// 			pivot_column_groupby: ["customer"],
// 			pivot_row_groupby: ["product_id"],
// 		},
// 	});

// 	assert.containsOnce(
// 		target,
// 		"thead .o_pivot_header_cell_opened",
// 		"column: should have one opened header"
// 	);
// 	assert.containsOnce(
// 		target,
// 		"thead .o_pivot_header_cell_closed:contains(First)",
// 		"column: should display one closed header with 'First'"
// 	);
// 	assert.containsOnce(
// 		target,
// 		"thead .o_pivot_header_cell_closed:contains(Second)",
// 		"column: should display one closed header with 'Second'"
// 	);

// 	assert.containsOnce(
// 		target,
// 		"tbody .o_pivot_header_cell_opened",
// 		"row: should have one opened header"
// 	);
// 	assert.containsOnce(
// 		target,
// 		"tbody .o_pivot_header_cell_closed:contains(xphone)",
// 		"row: should display one closed header with 'xphone'"
// 	);
// 	assert.containsOnce(
// 		target,
// 		"tbody .o_pivot_header_cell_closed:contains(xpad)",
// 		"row: should display one closed header with 'xpad'"
// 	);

// 	expect(target.querySelector("tbody tr").querySelectorAll("td")[2].innerText).toBe("32");
// });

// test("clear table cells data after closeGroup", async () => {
// 	expect.assertions(2);

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: "<pivot/>",
// 		groupBy: ["product_id"],
// 	});

// 	await contains("thead .o_pivot_header_cell_closed").click();
// 	await mouseEnter(target.querySelector(".o-dropdown--menu .dropdown-toggle"));
// 	await click(
// 		target.querySelectorAll(
// 			".o-overlay-item:nth-child(2) .o-dropdown--menu .dropdown-item"
// 		)[3]
// 	);

// 	// close and reopen row groupings after changing value
// 	serverData.models.partner.records.find((r) => r.product_id === 37).date = "2016-10-27";

// 	await contains("tbody .o_pivot_header_cell_opened").click();
// 	await contains("tbody .o_pivot_header_cell_closed").click();
// 	await contains(".o-dropdown--menu .dropdown-item:eq(4)").click();
// 	expect(.o_pivot_cell_value:eq(4).innerText).toBe(""); // xphone December 2016

// 	// invert axis, and reopen column groupings
// 	await contains(".o_pivot_buttons .o_pivot_flip_button").click();
// 	await contains("thead .o_pivot_header_cell_opened").click();
// 	await contains("thead .o_pivot_header_cell_closed").click();
// 	await contains(".o-dropdown--menu .dropdown-item:eq(4)").click();
// 	expect(.o_pivot_cell_value:eq(3).innerText).toBe(""); // December 2016 xphone
// });

// test("correctly group data after flip (1)", async () => {
// 	expect.assertions(4);

// 	serverData.views = {
// 		"partner,false,pivot": "<pivot/>",
// 		"partner,false,search": `<search><filter name="bayou" string="Bayou" domain="[(1,'=',1)]"/></search>`,
// 		"partner,false,list": '<tree><field name="foo"/></tree>',
// 		"partner,false,form": '<form><field name="foo"/></form>',
// 	};

// 	const webClient = await createWebClient({ serverData });

// 	await doAction(webClient, {
// 		res_model: "partner",
// 		type: "ir.actions.act_window",
// 		views: [[false, "pivot"]],
// 		context: { group_by: ["product_id"] },
// 	});

// 	assert.deepEqual(
// 		[...target.querySelectorAll("tbody th")].map((e) => e.innerText),
// 		["Total", "xphone", "xpad"]
// 	);

// 	// flip axis
// 	await contains(".o_pivot_flip_button").click();

// 	assert.deepEqual(
// 		[...target.querySelectorAll("tbody th")].map((e) => e.innerText),
// 		["Total"]
// 	);

// 	// select filter "Bayou" in control panel
// 	await toggleSearchBarMenu();
// 	await toggleMenuItem("Bayou");

// 	assert.deepEqual(
// 		[...target.querySelectorAll("tbody th")].map((e) => e.innerText),
// 		["Total", "xphone", "xpad"]
// 	);

// 	// close row header "Total"
// 	await contains("tbody .o_pivot_header_cell_opened").click();

// 	assert.deepEqual(
// 		[...target.querySelectorAll("tbody th")].map((e) => e.innerText),
// 		["Total"]
// 	);
// });

// test("correctly group data after flip (2)", async () => {
// 	expect.assertions(5);

// 	serverData.views = {
// 		"partner,false,pivot": "<pivot/>",
// 		"partner,false,search": `<search><filter name="bayou" string="Bayou" domain="[(1,'=',1)]"/></search>`,
// 		"partner,false,list": '<tree><field name="foo"/></tree>',
// 		"partner,false,form": '<form><field name="foo"/></form>',
// 	};

// 	const webClient = await createWebClient({ serverData });

// 	await doAction(webClient, {
// 		res_model: "partner",
// 		type: "ir.actions.act_window",
// 		views: [[false, "pivot"]],
// 		context: { group_by: ["product_id"] },
// 	});

// 	assert.deepEqual(
// 		[...target.querySelectorAll("tbody th")].map((e) => e.innerText),
// 		["Total", "xphone", "xpad"]
// 	);

// 	// select filter "Bayou" in control panel
// 	await toggleSearchBarMenu();
// 	await toggleMenuItem("Bayou");

// 	assert.deepEqual(
// 		[...target.querySelectorAll("tbody th")].map((e) => e.innerText),
// 		["Total", "xphone", "xpad"]
// 	);

// 	// flip axis
// 	await contains(".o_pivot_flip_button").click();

// 	assert.deepEqual(
// 		[...target.querySelectorAll("tbody th")].map((e) => e.innerText),
// 		["Total"]
// 	);

// 	// unselect filter "Bayou" in control panel
// 	await toggleSearchBarMenu();
// 	await toggleMenuItem("Bayou");

// 	assert.deepEqual(
// 		[...target.querySelectorAll("tbody th")].map((e) => e.innerText),
// 		["Total", "xphone", "xpad"]
// 	);

// 	// close row header "Total"
// 	await contains("tbody .o_pivot_header_cell_opened").click();

// 	assert.deepEqual(
// 		[...target.querySelectorAll("tbody th")].map((e) => e.innerText),
// 		["Total"]
// 	);
// });

// test("correctly uses pivot_ keys from the context (at reload)", async () => {
// 	expect.assertions(8);

// 	// in this test, we use "foo" as a measure
// 	serverData.models.partner.fields.foo.store = true;
// 	serverData.models.partner.fields.amount = {
// 		string: "Amount",
// 		type: "float",
// 		aggregator: "sum",
// 	};

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 			<pivot>
// 				<field name="date" interval="day" type="col"/>
// 				<field name="amount" type="measure"/>
// 			</pivot>`,
// 		searchViewArch: `
// 			<search>
// 				<filter
// 					name="filter_with_context"
// 					string="My fake favorite"
// 					domain="[]"
// 					context="{
// 						'pivot_measures': ['foo'],
// 						'pivot_column_groupby': ['customer'],
// 						'pivot_row_groupby': ['product_id']
// 					}"
// 				/>
// 			</search>`,
// 	});

// 	expect(target.querySelector("tbody tr").querySelectorAll("td.o_pivot_cell_value")[4].innerText).toBe("0.00");

// 	await toggleSearchBarMenu();
// 	await toggleMenuItem("My fake favorite");

// 	assert.containsOnce(
// 		target,
// 		"thead .o_pivot_header_cell_opened",
// 		"column: should have one opened header"
// 	);
// 	assert.containsOnce(
// 		target,
// 		"thead .o_pivot_header_cell_closed:contains(First)",
// 		"column: should display one closed header with 'First'"
// 	);
// 	assert.containsOnce(
// 		target,
// 		"thead .o_pivot_header_cell_closed:contains(Second)",
// 		"column: should display one closed header with 'Second'"
// 	);

// 	assert.containsOnce(
// 		target,
// 		"tbody .o_pivot_header_cell_opened",
// 		"row: should have one opened header"
// 	);
// 	assert.containsOnce(
// 		target,
// 		"tbody .o_pivot_header_cell_closed:contains(xphone)",
// 		"row: should display one closed header with 'xphone'"
// 	);
// 	assert.containsOnce(
// 		target,
// 		"tbody .o_pivot_header_cell_closed:contains(xpad)",
// 		"row: should display one closed header with 'xpad'"
// 	);

// 	expect(target.querySelector("tbody tr").querySelectorAll("td")[2].innerText).toBe("32");
// });

// test("correctly use group_by key from the context", async () => {
// 	expect.assertions(7);

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 			<pivot>
// 				<field name="customer" type="col" />
// 				<field name="foo" type="measure" />
// 			</pivot>`,
// 		groupBy: ["product_id"],
// 	});

// 	assert.containsOnce(
// 		target,
// 		"thead .o_pivot_header_cell_opened",
// 		"column: should have one opened header"
// 	);
// 	assert.containsOnce(
// 		target,
// 		"thead .o_pivot_header_cell_closed:contains(First)",
// 		'column: should display one closed header with "First"'
// 	);
// 	assert.containsOnce(
// 		target,
// 		"thead .o_pivot_header_cell_closed:contains(Second)",
// 		'column: should display one closed header with "Second"'
// 	);

// 	assert.containsOnce(
// 		target,
// 		"tbody .o_pivot_header_cell_opened",
// 		"row: should have one opened header"
// 	);
// 	assert.containsOnce(
// 		target,
// 		"tbody .o_pivot_header_cell_closed:contains(xphone)",
// 		'row: should display one closed header with "xphone"'
// 	);
// 	assert.containsOnce(
// 		target,
// 		"tbody .o_pivot_header_cell_closed:contains(xpad)",
// 		'row: should display one closed header with "xpad"'
// 	);

// 	expect(target.querySelector("tbody tr").querySelectorAll("td")[2].innerText).toBe("32");
// });

// test(
// 	"correctly uses pivot_row_groupby key with default groupBy from the context",
// 	async function (assert) {
// 		expect.assertions(6);

// 		serverData.models.partner.fields.amount = {
// 			string: "Amount",
// 			type: "float",
// 			aggregator: "sum",
// 		};

// 		await mountView({
// 			type: "pivot",
// 			resModel: "partner",
			
// 			arch: `
// 				<pivot>
// 					<field name="customer" type="col"/>
// 					<field name="date" interval="day" type="row"/>
// 				</pivot>`,
// 			groupBy: ["customer"],
// 			context: {
// 				pivot_row_groupby: ["product_id"],
// 			},
// 		});

// 		assert.containsOnce(
// 			target,
// 			"thead .o_pivot_header_cell_opened",
// 			"column: should have one opened header"
// 		);
// 		assert.containsOnce(
// 			target,
// 			"thead .o_pivot_header_cell_closed:contains(First)",
// 			"column: should display one closed header with 'First'"
// 		);
// 		assert.containsOnce(
// 			target,
// 			"thead .o_pivot_header_cell_closed:contains(Second)",
// 			"column: should display one closed header with 'Second'"
// 		);

// 		// With pivot_row_groupby, groupBy customer should replace and eventually display product_id
// 		assert.containsOnce(
// 			target,
// 			"tbody .o_pivot_header_cell_opened",
// 			"row: should have one opened header"
// 		);
// 		assert.containsOnce(
// 			target,
// 			"tbody .o_pivot_header_cell_closed:contains(xphone)",
// 			"row: should display one closed header with 'xphone'"
// 		);
// 		assert.containsOnce(
// 			target,
// 			"tbody .o_pivot_header_cell_closed:contains(xpad)",
// 			"row: should display one closed header with 'xpad'"
// 		);
// 	}
// );

// test("pivot still handles __count__ measure", async () => {
// 	serverData.models.partner.fields.computed_field.aggregator = undefined;
// 	serverData.models.partner.fields.foo.aggregator = undefined;

// 	// for retro-compatibility reasons, the pivot view still handles
// 	// '__count__' measure.
// 	expect.assertions(4);

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: "<pivot></pivot>",
// 		mockRPC(route, args) {
// 			if (args.method === "read_group") {
// 				assert.deepEqual(
// 					args.kwargs.fields,
// 					["__count"],
// 					"should make a read_group with field __count"
// 				);
// 			}
// 		},
// 		context: {
// 			pivot_measures: ["__count__"],
// 		},
// 	});

// 	await contains(".o_pivot_buttons button.dropdown-toggle").click();
// 	const dropdownMenu = getDropdownMenu(target, ".o_pivot_buttons button.dropdown-toggle");
// 	assert.containsOnce(dropdownMenu, ".dropdown-item");
// 	expect(dropdownMenu.querySelector(".dropdown-item").innerText).toBe("Count");
// 	assert.hasClass(dropdownMenu.querySelector(".dropdown-item"), "selected");
// });

// test("not use a many2one as a measure by default", async () => {
// 	serverData.models.partner.fields.computed_field.aggregator = undefined;
// 	serverData.models.partner.fields.foo.aggregator = undefined;
// 	expect.assertions(3);

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 			<pivot>
// 				<field name="product_id"/>
// 				<field name="date" interval="month" type="col"/>
// 			</pivot>`,
// 	});
// 	await contains(".o_pivot_buttons button.dropdown-toggle").click();
// 	const dropdownMenu = getDropdownMenu(target, ".o_pivot_buttons button.dropdown-toggle");
// 	assert.containsOnce(dropdownMenu, ".dropdown-item");
// 	expect(dropdownMenu.querySelector(".dropdown-item").innerText).toBe("Count");
// 	assert.hasClass(dropdownMenu.querySelector(".dropdown-item"), "selected");
// });

// test("pivot view with many2one field as a measure", async () => {
// 	expect.assertions(1);

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 			<pivot>
// 				<field name="product_id" type="measure"/>
// 				<field name="date" interval="month" type="col"/>
// 			</pivot>`,
// 	});

// 	expect(target.querySelector("table tbody tr").innerText.replace(/\s/g, "")).toBe("Total1122");
// });

// test("pivot view with reference field as a measure", async () => {
// 	expect.assertions(1);

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 			<pivot>
// 				<field name="ref" type="measure"/>
// 				<field name="date" interval="month" type="col"/>
// 			</pivot>`,
// 	});

// 	expect(target.querySelector("table tbody tr").innerText.replace(/\s/g, "")).toBe("Total1124");
// });

// test("m2o as measure, drilling down into data", async () => {
// 	expect.assertions(1);

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 			<pivot>
// 				<field name="product_id" type="measure"/>
// 			</pivot>`,
// 	});
// 	await contains("tbody .o_pivot_header_cell_closed").click();
// 	// click on date by month
// 	const dropdownMenu = getDropdownMenu(target, "tbody .o_pivot_header_cell_closed");
// 	await mouseEnter(dropdownMenu.querySelector(".dropdown-toggle"));
// 	const subdropdownMenu = getDropdownMenu(target, ".dropdown-toggle");
// 	await contains("subdropdownMenu.querySelectorAll(".dropdown-item")[3]").click();

// 	expect([...target.querySelectorAll(".o_pivot_cell_value")].map((c) => c.innerText).join("")).toBe("2112");
// });

// test("Row and column groupbys plus a domain", async () => {
// 	expect.assertions(3);

// 	const expectedContext = {
// 		group_by: [],
// 		pivot_column_groupby: ["customer"],
// 		pivot_measures: ["foo"],
// 		pivot_row_groupby: ["product_id"],
// 	};
// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 			<pivot>
// 				<field name="foo" type="measure"/>
// 			</pivot>`,
// 		searchViewArch: `
// 			<search>
// 				<filter name="some_filter" string="Some Filter" domain="[('product_id', '=', 41)]"/>
// 			</search>`,
// 		mockRPC(route, args) {
// 			if (args.method === "create_or_replace") {
// 				assert.deepEqual(args.args[0].context, expectedContext);
// 				return true;
// 			}
// 		},
// 	});

// 	// Set a column groupby
// 	await contains("thead .o_pivot_header_cell_closed").click();
// 	await contains(".o-dropdown--menu .dropdown-item:eq(1)").click();

// 	// Set a Row groupby
// 	await contains("tbody .o_pivot_header_cell_closed").click();
// 	await contains(".o-dropdown--menu .dropdown-item:eq(4)").click();

// 	// Add a filter
// 	await toggleSearchBarMenu();
// 	await toggleMenuItem("Some Filter");

// 	assert.containsOnce(
// 		target,
// 		"tbody .o_pivot_header_cell_closed",
// 		"There should be only one product line because of the domain"
// 	);
// 	expect(target.querySelector("tbody .o_pivot_header_cell_closed").innerText).toBe("xpad");

// 	// Save current search to favorite
// 	await toggleSaveFavorite(target);
// 	await editFavoriteName(target, "My favorite");
// 	await saveFavorite(target);
// });

// test(
// 	"parallel data loading should discard all but the last one",
// 	async function (assert) {
// 		expect.assertions(6);

// 		let def;
// 		await mountView({
// 			type: "pivot",
// 			resModel: "partner",
			
// 			arch: `
// 				<pivot>
// 					<field name="foo" type="measure"/>
// 				</pivot>`,
// 			searchViewArch: `
// 				<search>
// 					<filter string="Product" name="product_id" context="{'group_by':'product_id'}"/>
// 					<filter string="Customer" name="customer" context="{'group_by':'customer'}"/>
// 				</search>`,
// 			mockRPC(route, args) {
// 				if (args.method === "read_group") {
// 					return Promise.resolve(def);
// 				}
// 			},
// 		});

// 		expect(".o_pivot_cell_value", "should have 1 cell initially").toHaveCount(1);
// 		expect("tbody tr", "should have 1 row initially").toHaveCount(1);

// 		def = new Deferred();
// 		await toggleSearchBarMenu();
// 		await toggleMenuItem("Product");
// 		await toggleMenuItem("Customer");

// 		expect(".o_pivot_cell_value", "should still have 1 cell").toHaveCount(1);
// 		expect("tbody tr", "should still have 1 row").toHaveCount(1);

// 		await def.resolve();
// 		await animationFrame();

// 		expect(".o_pivot_cell_value").toHaveCount(6);
// 		expect("tbody tr").toHaveCount(6);
// 	}
// );

// test("pivot measures should be alphabetically sorted", async () => {
// 	serverData.models.partner.fields.computed_field.aggregator = undefined;
// 	expect.assertions(1);

// 	// It's important to compare capitalized and lowercased words
// 	// to be sure the sorting is effective with both of them
// 	serverData.models.partner.fields.bouh = {
// 		string: "bouh",
// 		type: "integer",
// 		aggregator: "sum",
// 	};
// 	serverData.models.partner.fields.modd = {
// 		string: "modd",
// 		type: "integer",
// 		aggregator: "sum",
// 	};
// 	serverData.models.partner.fields.zip = {
// 		string: "Zip",
// 		type: "integer",
// 		aggregator: "sum",
// 	};

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 			<pivot>
// 				<field name="zip" type="measure"/>
// 				<field name="foo" type="measure"/>
// 				<field name="bouh" type="measure"/>
// 				<field name="modd" type="measure"/>
// 			</pivot>`,
// 	});

// 	await contains(".o_pivot_buttons button.dropdown-toggle").click();
// 	assert.strictEqual(
// 		[...target.querySelectorAll(".o-dropdown--menu .dropdown-item")]
// 			.map((i) => i.innerText)
// 			.join(""),
// 		"bouhFoomoddZipCount"
// 	);
// });

// test("pivot view should use default order for auto sorting", async () => {
// 	expect.assertions(1);

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 			<pivot default_order="foo asc">
// 				<field name="foo" type="measure"/>
// 			</pivot>`,
// 	});

// 	assert.hasClass(
// 		target.querySelector("thead th.o_pivot_measure_row"),
// 		"o_pivot_sort_order_asc"
// 	);
// });

// test("pivot view can be flipped", async () => {
// 	expect.assertions(5);

// 	var rpcCount = 0;

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 			<pivot>
// 				<field name="product_id" type="row"/>
// 			</pivot>`,
// 		mockRPC() {
// 			rpcCount++;
// 		},
// 	});

// 	expect("tbody tr").toHaveCount(3);
// 	let values = ["4", "1", "3"];
// 	expect(getCurrentValues()).toBe(values.join());

// 	rpcCount = 0;
// 	await contains(".o_pivot_flip_button").click();

// 	expect(rpcCount).toEqual(0);
// 	expect("tbody tr", "should have 1 rows: 1 for the main header").toHaveCount(1);

// 	values = ["1", "3", "4"];
// 	expect(getCurrentValues()).toBe(values.join());
// });

// test("rendering of pivot view with comparison", async () => {
// 	serverData.models.partner.fields.computed_field.aggregator = undefined;

// 	serverData.models.partner.records[0].date = "2016-12-15";
// 	serverData.models.partner.records[1].date = "2016-12-17";
// 	serverData.models.partner.records[2].date = "2016-11-22";
// 	serverData.models.partner.records[3].date = "2016-11-03";

// 	patchDate(2016, 11, 20, 1, 0, 0);

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 			<pivot>
// 				<field name="date" interval="month" type="col"/>
// 				<field name="foo" type="measure"/>
// 			</pivot>`,
// 		searchViewArch: `
// 			<search>
// 				<filter name="date_filter" date="date" domain="[]" default_period='last_year'/>
// 			</search>`,
// 		context: { search_default_date_filter: 1 },
// 		mockRPC(route, args) {
// 			if (args.method === "create_or_replace") {
// 				assert.deepEqual(args.args[0].context, {
// 					pivot_measures: ["__count"],
// 					pivot_column_groupby: [],
// 					pivot_row_groupby: ["product_id"],
// 					group_by: [],
// 					comparison: {
// 						comparisonId: "previous_period",
// 						comparisonRange: [
// 							"&",
// 							["date", ">=", "2016-11-01"],
// 							["date", "<=", "2016-11-30"],
// 						],
// 						comparisonRangeDescription: "November 2016",
// 						fieldDescription: "Date",
// 						fieldName: "date",
// 						range: [
// 							"&",
// 							["date", ">=", "2016-12-01"],
// 							["date", "<=", "2016-12-31"],
// 						],
// 						rangeDescription: "December 2016",
// 					},
// 				});
// 				return true;
// 			}
// 		},
// 	});

// 	// with no data
// 	await toggleSearchBarMenu();
// 	await toggleMenuItem("Date: Previous period");

// 	expect("p.o_view_nocontent_empty_folder").toHaveCount(1);

// 	await toggleMenuItem("Date");
// 	await toggleMenuItemOption("Date", "December");
// 	await toggleMenuItemOption("Date", "2016");
// 	await toggleMenuItemOption("Date", "2015");

// 	expect(".o_pivot thead tr:last th").toHaveCount(9);
// 	let values = ["19", "0", "-100%", "0", "13", "100%", "19", "13", "-31.58%"];
// 	expect(getCurrentValues()).toBe(values.join());

// 	// with data, with row groupby
// 	await contains("tbody .o_pivot_header_cell_closed").click();
// 	await contains(".o-dropdown--menu .dropdown-item:eq(4)").click();
// 	values = [
// 		"19",
// 		"0",
// 		"-100%",
// 		"0",
// 		"13",
// 		"100%",
// 		"19",
// 		"13",
// 		"-31.58%",
// 		"19",
// 		"0",
// 		"-100%",
// 		"0",
// 		"1",
// 		"100%",
// 		"19",
// 		"1",
// 		"-94.74%",
// 		"0",
// 		"12",
// 		"100%",
// 		"0",
// 		"12",
// 		"100%",
// 	];
// 	expect(getCurrentValues()).toBe(values.join());

// 	await contains(".o_pivot_buttons button.dropdown-toggle").click();

// 	await contains(".o-dropdown--menu .dropdown-item:eq(0)").click();
// 	await contains(".o-dropdown--menu .dropdown-item:eq(1)").click();
// 	values = ["2,0,-100%,0,2,100%,2,2,0%,2,0,-100%,0,1,100%,2,1,-50%,0,1,100%,0,1,100%"];
// 	expect(getCurrentValues()).toBe(values.join());

// 	await contains("thead .o_pivot_header_cell_opened").click();
// 	values = ["2", "2", "0%", "2", "1", "-50%", "0", "1", "100%"];
// 	expect(getCurrentValues()).toBe(values.join());

// 	await toggleSearchBarMenu();
// 	await toggleSaveFavorite(target);
// 	await editFavoriteName(target, "Fav");
// 	await saveFavorite(target);
// });

// test("export data in excel with comparison", async () => {
// 	expect.assertions(12);

// 	serverData.models.partner.records[0].date = "2016-12-15";
// 	serverData.models.partner.records[1].date = "2016-12-17";
// 	serverData.models.partner.records[2].date = "2016-11-22";
// 	serverData.models.partner.records[3].date = "2016-11-03";

// 	patchDate(2016, 11, 20, 1, 0, 0);

// 	mockDownload(({ url, data }) => {
// 		data = JSON.parse(data.data);
// 		for (const l of data.col_group_headers) {
// 			const titles = l.map((o) => o.title);
// 			assert.step(JSON.stringify(titles));
// 		}
// 		const measures = data.measure_headers.map((o) => o.title);
// 		assert.step(JSON.stringify(measures));
// 		const origins = data.origin_headers.map((o) => o.title);
// 		assert.step(JSON.stringify(origins));
// 		assert.step(String(data.measure_count));
// 		assert.step(String(data.origin_count));
// 		const valuesLength = data.rows.map((o) => o.values.length);
// 		assert.step(JSON.stringify(valuesLength));
// 		expect(url).toBe("/web/pivot/export_xlsx");
// 		return Promise.resolve();
// 	});

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 			<pivot>
// 				<field name="date" interval="month" type="col"/>
// 				<field name="foo" type="measure"/>
// 			</pivot>`,
// 		searchViewArch: `
// 			<search>
// 				<filter name="date_filter" date="date" domain="[]" default_period='antepenultimate_month'/>
// 			</search>`,
// 		context: { search_default_date_filter: 1 },
// 	});

// 	// open comparison menu
// 	await toggleSearchBarMenu();
// 	// compare October 2016 to September 2016
// 	await toggleMenuItem("Date: Previous period");

// 	// With the data above, the time ranges contain no record.
// 	expect("p.o_view_nocontent_empty_folder", "there should be no data").toHaveCount(1);
// 	// export data should be impossible since the pivot buttons
// 	// are deactivated (exception: the 'Measures' button).
// 	assert.ok(target.querySelector(".o_pivot_buttons button.o_pivot_download").disabled);

// 	await toggleMenuItem("Date");
// 	await toggleMenuItemOption("Date", "December");
// 	await toggleMenuItemOption("Date", "October");
// 	assert.notOk(target.querySelector(".o_pivot_buttons button.o_pivot_download").disabled);

// 	// With the data above, the time ranges contain some records.
// 	// export data. Should execute 'get_file'
// 	await contains(".o_pivot_buttons button.o_pivot_download").click();

// 	assert.verifySteps([
// 		// col group headers
// 		'["Total",""]',
// 		'["November 2016","December 2016"]',
// 		// measure headers
// 		'["Foo","Foo","Foo"]',
// 		// origin headers
// 		'["November 2016","December 2016","Variation","November 2016","December 2016"' +
// 			',"Variation","November 2016","December 2016","Variation"]',
// 		// number of 'measures'
// 		"1",
// 		// number of 'origins'
// 		"2",
// 		// rows values length
// 		"[9]",
// 	]);
// });

// test("rendering pivot view with comparison and count measure", async () => {
// 	expect.assertions(2);

// 	let mockMock = false;
// 	let nbReadGroup = 0;

// 	serverData.models.partner.records[0].date = "2016-12-15";
// 	serverData.models.partner.records[1].date = "2016-12-17";
// 	serverData.models.partner.records[2].date = "2016-12-22";
// 	serverData.models.partner.records[3].date = "2016-12-03";

// 	patchDate(2016, 11, 20, 1, 0, 0);

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: '<pivot><field name="customer" type="row"/></pivot>',
// 		searchViewArch: `
// 			<search>
// 				<filter name="date_filter" date="date" domain="[]" default_period='this_month'/>
// 			</search>`,
// 		context: { search_default_date_filter: 1 },
// 		mockRPC(route, args) {
// 			if (args.method === "read_group" && mockMock) {
// 				nbReadGroup++;
// 				if (nbReadGroup === 4) {
// 					// this modification is necessary because mockReadGroup does not
// 					// properly reflect the server response when there is no record
// 					// and a groupby list of length at least one.
// 					return Promise.resolve([{}]);
// 				}
// 			}
// 		},
// 	});

// 	mockMock = true;

// 	// compare December 2016 to November 2016
// 	await toggleSearchBarMenu();
// 	await toggleMenuItem("Date: Previous period");

// 	const values = ["0", "4", "100%", "0", "2", "100%", "0", "2", "100%"];
// 	expect(getCurrentValues()).toBe(values.join(","));
// 	expect(".o_pivot_header_cell_closed").toHaveCount(3);
// });

// test(
// 	"can sort a pivot view with comparison by clicking on header",
// 	async function (assert) {
// 		expect.assertions(6);

// 		serverData.models.partner.records[0].date = "2016-12-15";
// 		serverData.models.partner.records[1].date = "2016-12-17";
// 		serverData.models.partner.records[2].date = "2016-11-22";
// 		serverData.models.partner.records[3].date = "2016-11-03";

// 		patchDate(2016, 11, 20, 1, 0, 0);
// 		await mountView({
// 			type: "pivot",
// 			resModel: "partner",
			
// 			arch: `
// 				<pivot>
// 					<field name="date" interval="day" type="row"/>
// 					<field name="company_type" type="col"/>
// 					<field name="foo" type="measure"/>
// 				</pivot>`,
// 			searchViewArch: `
// 				<search>
// 					<filter name="date_filter" date="date" domain="[]" default_period='this_month'/>
// 				</search>`,
// 			context: { search_default_date_filter: 1 },
// 		});

// 		// compare December 2016 to November 2016
// 		await toggleSearchBarMenu();
// 		await toggleMenuItem("Date: Previous period");

// 		// initial sanity check
// 		let values = [
// 			"17",
// 			"12",
// 			"-29.41%",
// 			"2",
// 			"1",
// 			"-50%",
// 			"19",
// 			"13",
// 			"-31.58%",
// 			"2",
// 			"0",
// 			"-100%",
// 			"2",
// 			"0",
// 			"-100%",
// 			"17",
// 			"0",
// 			"-100%",
// 			"17",
// 			"0",
// 			"-100%",
// 			"0",
// 			"12",
// 			"100%",
// 			"0",
// 			"12",
// 			"100%",
// 			"0",
// 			"1",
// 			"100%",
// 			"0",
// 			"1",
// 			"100%",
// 		];
// 		expect(getCurrentValues()).toBe(values.join());

// 		// click on 'Foo' in column Total/Company (should sort by the period of interest, ASC)
// 		await contains(".o_pivot_measure_row").click();
// 		values = [
// 			"17",
// 			"12",
// 			"-29.41%",
// 			"2",
// 			"1",
// 			"-50%",
// 			"19",
// 			"13",
// 			"-31.58%",
// 			"2",
// 			"0",
// 			"-100%",
// 			"2",
// 			"0",
// 			"-100%",
// 			"0",
// 			"12",
// 			"100%",
// 			"0",
// 			"12",
// 			"100%",
// 			"0",
// 			"1",
// 			"100%",
// 			"0",
// 			"1",
// 			"100%",
// 			"17",
// 			"0",
// 			"-100%",
// 			"17",
// 			"0",
// 			"-100%",
// 		];
// 		expect(getCurrentValues()).toBe(values.join());

// 		// click again on 'Foo' in column Total/Company (should sort by the period of interest, DESC)
// 		await contains(".o_pivot_measure_row").click();
// 		values = [
// 			"17",
// 			"12",
// 			"-29.41%",
// 			"2",
// 			"1",
// 			"-50%",
// 			"19",
// 			"13",
// 			"-31.58%",
// 			"17",
// 			"0",
// 			"-100%",
// 			"17",
// 			"0",
// 			"-100%",
// 			"2",
// 			"0",
// 			"-100%",
// 			"2",
// 			"0",
// 			"-100%",
// 			"0",
// 			"12",
// 			"100%",
// 			"0",
// 			"12",
// 			"100%",
// 			"0",
// 			"1",
// 			"100%",
// 			"0",
// 			"1",
// 			"100%",
// 		];
// 		expect(getCurrentValues()).toBe(values.join());

// 		// click on 'This Month' in column Total/Individual/Foo
// 		await contains(".o_pivot_origin_row:eq(3)").click();
// 		values = [
// 			"17",
// 			"12",
// 			"-29.41%",
// 			"2",
// 			"1",
// 			"-50%",
// 			"19",
// 			"13",
// 			"-31.58%",
// 			"17",
// 			"0",
// 			"-100%",
// 			"17",
// 			"0",
// 			"-100%",
// 			"0",
// 			"12",
// 			"100%",
// 			"0",
// 			"12",
// 			"100%",
// 			"0",
// 			"1",
// 			"100%",
// 			"0",
// 			"1",
// 			"100%",
// 			"2",
// 			"0",
// 			"-100%",
// 			"2",
// 			"0",
// 			"-100%",
// 		];
// 		expect(getCurrentValues()).toBe(values.join());

// 		// click on 'Previous Period' in column Total/Individual/Foo
// 		await contains(".o_pivot_origin_row:eq(4)").click();
// 		values = [
// 			"17",
// 			"12",
// 			"-29.41%",
// 			"2",
// 			"1",
// 			"-50%",
// 			"19",
// 			"13",
// 			"-31.58%",
// 			"2",
// 			"0",
// 			"-100%",
// 			"2",
// 			"0",
// 			"-100%",
// 			"17",
// 			"0",
// 			"-100%",
// 			"17",
// 			"0",
// 			"-100%",
// 			"0",
// 			"12",
// 			"100%",
// 			"0",
// 			"12",
// 			"100%",
// 			"0",
// 			"1",
// 			"100%",
// 			"0",
// 			"1",
// 			"100%",
// 		];
// 		expect(getCurrentValues()).toBe(values.join());

// 		// click on 'Variation' in column Total/Foo
// 		await contains(".o_pivot_origin_row:eq(8)").click();
// 		values = [
// 			"17",
// 			"12",
// 			"-29.41%",
// 			"2",
// 			"1",
// 			"-50%",
// 			"19",
// 			"13",
// 			"-31.58%",
// 			"2",
// 			"0",
// 			"-100%",
// 			"2",
// 			"0",
// 			"-100%",
// 			"17",
// 			"0",
// 			"-100%",
// 			"17",
// 			"0",
// 			"-100%",
// 			"0",
// 			"12",
// 			"100%",
// 			"0",
// 			"12",
// 			"100%",
// 			"0",
// 			"1",
// 			"100%",
// 			"0",
// 			"1",
// 			"100%",
// 		];
// 		expect(getCurrentValues()).toBe(values.join());
// 	}
// );

// test("Click on the measure list but not on a menu item", async () => {
// 	expect.assertions(4);

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		// have at least a measure to have a separator in the Measures dropdown:
// 		//
// 		// Foo
// 		// -----
// 		// Count
// 		arch: `<pivot><field name="foo" type="measure"/></pivot>`,
// 	});

// 	expect(".o-dropdown--menu").toHaveCount(0);

// 	// open the "Measures" menu
// 	await contains(".o_pivot_buttons .dropdown-toggle").click();
// 	expect(".o-dropdown--menu").toHaveCount(1);

// 	// click on the divider in the "Measures" menu does not crash
// 	await contains(".o-dropdown--menu .dropdown-divider").click();
// 	// the menu should still be open
// 	expect(".o-dropdown--menu").toHaveCount(1);

// 	// click on the measure list but not on a menu item or the separator
// 	await contains(".o-dropdown--menu").click();
// 	// the menu should still be open
// 	expect(".o-dropdown--menu").toHaveCount(1);
// });

// test(
// 	"Navigation list view for a group and back with breadcrumbs",
// 	async function (assert) {
// 		expect.assertions(16);

// 		serverData.views = {
// 			"partner,false,pivot": `
// 				<pivot>
// 					<field name="customer" type="row"/>
// 				</pivot>`,
// 			"partner,false,search": `
// 				<search>
// 					<filter name="bayou" string="Bayou" domain="[('foo','=', 12)]"/>
// 				</search>`,
// 			"partner,false,list": '<tree><field name="foo"/></tree>',
// 			"partner,false,form": '<form><field name="foo"/></form>',
// 		};

// 		let readGroupCount = 0;
// 		const mockRPC = (route, args) => {
// 			if (args.method === "read_group") {
// 				assert.step("read_group");
// 				const domain = args.kwargs.domain;
// 				if ([0, 1].indexOf(readGroupCount) !== -1) {
// 					assert.deepEqual(domain, [], "domain empty");
// 				} else if ([2, 3, 4, 5].indexOf(readGroupCount) !== -1) {
// 					assert.deepEqual(
// 						domain,
// 						[["foo", "=", 12]],
// 						"domain conserved when back with breadcrumbs"
// 					);
// 				}
// 				readGroupCount++;
// 			}
// 			if (args.method === "web_search_read") {
// 				assert.step("web_search_read");
// 				const domain = args.kwargs.domain;
// 				assert.deepEqual(
// 					domain,
// 					["&", ["customer", "=", 1], ["foo", "=", 12]],
// 					"list domain is correct"
// 				);
// 			}
// 		};

// 		const webClient = await createWebClient({  mockRPC });

// 		await doAction(webClient, {
// 			res_model: "partner",
// 			type: "ir.actions.act_window",
// 			views: [[false, "pivot"]],
// 		});

// 		await toggleSearchBarMenu();
// 		await toggleMenuItem(0);
// 		await animationFrame();

// 		await contains(".o_pivot_cell_value:eq(1)").click();

// 		expect(".o_list_view").toHaveCount(1);

// 		await contains(".o_control_panel ol.breadcrumb li.breadcrumb-item").click();

// 		assert.verifySteps([
// 			"read_group",
// 			"read_group",
// 			"read_group",
// 			"read_group",
// 			"web_search_read",
// 			"read_group",
// 			"read_group",
// 		]);
// 	}
// );

// test(
// 	"Cell values are kept when flippin a pivot view in comparison mode",
// 	async function (assert) {
// 		expect.assertions(2);

// 		serverData.models.partner.records[0].date = "2016-12-15";
// 		serverData.models.partner.records[1].date = "2016-12-17";
// 		serverData.models.partner.records[2].date = "2016-11-22";
// 		serverData.models.partner.records[3].date = "2016-11-03";

// 		patchDate(2016, 11, 20, 1, 0, 0);
// 		await mountView({
// 			type: "pivot",
// 			resModel: "partner",
			
// 			arch: `
// 				<pivot>
// 					<field name="date" interval="day" type="row"/>
// 					<field name="company_type" type="col"/>
// 					<field name="foo" type="measure"/>
// 				</pivot>`,
// 			searchViewArch: `
// 				<search>
// 					<filter name="date_filter" date="date" domain="[]" default_period='this_month'/>
// 				</search>`,
// 			context: { search_default_date_filter: 1 },
// 		});

// 		// compare December 2016 to November 2016
// 		await toggleSearchBarMenu();
// 		await toggleMenuItem("Date: Previous period");

// 		// initial sanity check
// 		let values = [
// 			"17",
// 			"12",
// 			"-29.41%",
// 			"2",
// 			"1",
// 			"-50%",
// 			"19",
// 			"13",
// 			"-31.58%",
// 			"2",
// 			"0",
// 			"-100%",
// 			"2",
// 			"0",
// 			"-100%",
// 			"17",
// 			"0",
// 			"-100%",
// 			"17",
// 			"0",
// 			"-100%",
// 			"0",
// 			"12",
// 			"100%",
// 			"0",
// 			"12",
// 			"100%",
// 			"0",
// 			"1",
// 			"100%",
// 			"0",
// 			"1",
// 			"100%",
// 		];
// 		expect(getCurrentValues()).toBe(values.join());

// 		// flip table
// 		await contains(".o_pivot_flip_button").click();

// 		values = [
// 			"2",
// 			"0",
// 			"-100%",
// 			"17",
// 			"0",
// 			"-100%",
// 			"0",
// 			"12",
// 			"100%",
// 			"0",
// 			"1",
// 			"100%",
// 			"19",
// 			"13",
// 			"-31.58%",
// 			"17",
// 			"0",
// 			"-100%",
// 			"0",
// 			"12",
// 			"100%",
// 			"17",
// 			"12",
// 			"-29.41%",
// 			"2",
// 			"0",
// 			"-100%",
// 			"0",
// 			"1",
// 			"100%",
// 			"2",
// 			"1",
// 			"-50%",
// 		];
// 		expect(getCurrentValues()).toBe(values.join());
// 	}
// );

// test("Flip then compare, table col groupbys are kept", async () => {
// 	expect.assertions(6);

// 	serverData.models.partner.records[0].date = "2016-12-15";
// 	serverData.models.partner.records[1].date = "2016-12-17";
// 	serverData.models.partner.records[2].date = "2016-11-22";
// 	serverData.models.partner.records[3].date = "2016-11-03";

// 	patchDate(2016, 11, 20, 1, 0, 0);
// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 			<pivot>
// 				<field name="date" interval="day" type="row"/>
// 				<field name="company_type" type="col"/>
// 				<field name="foo" type="measure"/>
// 			</pivot>`,
// 		searchViewArch: `
// 			<search>
// 				<filter name="date_filter" date="date" domain="[]" default_period='this_month'/>
// 			</search>`,
// 	});

// 	assert.deepEqual(
// 		[...target.querySelectorAll("thead th")].map((th) => th.innerText),
// 		["", "Total", "", "Company", "individual", "Foo", "Foo", "Foo"],
// 		"The col headers should be as expected"
// 	);
// 	assert.deepEqual(
// 		[...target.querySelectorAll("tbody th")].map((th) => th.innerText),
// 		["Total", "2016-11-03", "2016-11-22", "2016-12-15", "2016-12-17"],
// 		"The row headers should be as expected"
// 	);

// 	// flip
// 	await contains(".o_pivot_flip_button").click();

// 	assert.deepEqual(
// 		[...target.querySelectorAll("thead th")].map((th) => th.innerText),
// 		[
// 			"",
// 			"Total",
// 			"",
// 			"2016-11-03",
// 			"2016-11-22",
// 			"2016-12-15",
// 			"2016-12-17",
// 			"Foo",
// 			"Foo",
// 			"Foo",
// 			"Foo",
// 			"Foo",
// 		],
// 		"The col headers should be as expected"
// 	);
// 	assert.deepEqual(
// 		[...target.querySelectorAll("tbody th")].map((th) => th.innerText),
// 		["Total", "Company", "individual"],
// 		"The row headers should be as expected"
// 	);

// 	// Filter on December 2016
// 	await toggleSearchBarMenu();
// 	await toggleMenuItem("Date");
// 	await toggleMenuItemOption("Date", "December");

// 	// compare December 2016 to November 2016
// 	await toggleMenuItem("Date: Previous period");

// 	assert.deepEqual(
// 		[...target.querySelectorAll("thead th")].map((th) => th.innerText),
// 		[
// 			"",
// 			"Total",
// 			"",
// 			"2016-11-03",
// 			"2016-11-22",
// 			"2016-12-15",
// 			"2016-12-17",
// 			"Foo",
// 			"Foo",
// 			"Foo",
// 			"Foo",
// 			"Foo",
// 			"November 2016",
// 			"December 2016",
// 			"Variation",
// 			"November 2016",
// 			"December 2016",
// 			"Variation",
// 			"November 2016",
// 			"December 2016",
// 			"Variation",
// 			"November 2016",
// 			"December 2016",
// 			"Variation",
// 			"November 2016",
// 			"December 2016",
// 			"Variation",
// 		],
// 		"The col headers should be as expected"
// 	);
// 	assert.deepEqual(
// 		[...target.querySelectorAll("tbody th")].map((th) => th.innerText),
// 		["Total", "Company", "individual"],
// 		"The row headers should be as expected"
// 	);
// });

// test(
// 	"correctly compute group domain when a date field has false value",
// 	async function (assert) {
// 		expect.assertions(1);

// 		serverData.models.partner.records.forEach((r) => (r.date = false));

// 		patchDate(2016, 11, 20, 1, 0, 0);

// 		const fakeActionService = {
// 			start() {
// 				return {
// 					doAction(action) {
// 						assert.deepEqual(action.domain, [["date", "=", false]]);
// 						return Promise.resolve(true);
// 					},
// 				};
// 			},
// 		};
// 		serviceRegistry.add("action", fakeActionService, { force: true });

// 		await mountView({
// 			type: "pivot",
// 			resModel: "partner",
			
// 			arch: `
// 				<pivot o_enable_linking="1">
// 					<field name="date" interval="day" type="row"/>
// 				</pivot>`,
// 		});

// 		await contains(".o_value:eq(1)").click();
// 	}
// );
// test(
// 	"Does not identify 'false' with false as keys when creating group trees",
// 	async function (assert) {
// 		expect.assertions(2);

// 		serverData.models.partner.fields.favorite_animal = {
// 			string: "Favorite animal",
// 			type: "char",
// 			store: true,
// 		};
// 		serverData.models.partner.records[0].favorite_animal = "Dog";
// 		serverData.models.partner.records[1].favorite_animal = "false";
// 		serverData.models.partner.records[2].favorite_animal = "None";

// 		patchDate(2016, 11, 20, 1, 0, 0);
// 		await mountView({
// 			type: "pivot",
// 			resModel: "partner",
			
// 			arch: `
// 				<pivot o_enable_linking="1">
// 					<field name="favorite_animal" type="row"/>
// 				</pivot>`,
// 		});

// 		assert.deepEqual(
// 			[...target.querySelectorAll("thead th")].map((th) => th.innerText),
// 			["", "Total", "Count"],
// 			"The col headers should be as expected"
// 		);
// 		assert.deepEqual(
// 			[...target.querySelectorAll("tbody th")].map((th) => th.innerText),
// 			["Total", "Dog", "None", "false", "None"],
// 			"The row headers should be as expected"
// 		);
// 	}
// );

// test(
// 	"group bys added via control panel and expand Header do not stack",
// 	async function (assert) {
// 		expect.assertions(8);

// 		await mountView({
// 			type: "pivot",
// 			resModel: "partner",
			
// 			arch: `
// 				<pivot>
// 					<field name="foo" type="measure"/>
// 				</pivot>`,
// 		});

// 		assert.deepEqual(
// 			[...target.querySelectorAll("thead th")].map((th) => th.innerText),
// 			["", "Total", "Foo"],
// 			"The col headers should be as expected"
// 		);
// 		assert.deepEqual(
// 			[...target.querySelectorAll("tbody th")].map((th) => th.innerText),
// 			["Total"],
// 			"The row headers should be as expected"
// 		);

// 		// open group by menu and add new groupby
// 		await toggleSearchBarMenu();
// 		await contains(`.o_add_custom_group_menu`).select("company_type");

// 		assert.deepEqual(
// 			[...target.querySelectorAll("thead th")].map((th) => th.innerText),
// 			["", "Total", "Foo"],
// 			"The col headers should be as expected"
// 		);
// 		assert.deepEqual(
// 			[...target.querySelectorAll("tbody th")].map((th) => th.innerText),
// 			["Total", "Company", "individual"],
// 			"The row headers should be as expected"
// 		);

// 		// Set a Row groupby
// 		await contains("tbody tr:nth-child(2) .o_pivot_header_cell_closed").click();
// 		await contains(".o-dropdown--menu .o_menu_item:nth-child(5)").click();

// 		assert.deepEqual(
// 			[...target.querySelectorAll("thead th")].map((th) => th.innerText),
// 			["", "Total", "Foo"],
// 			"The col headers should be as expected"
// 		);
// 		assert.deepEqual(
// 			[...target.querySelectorAll("tbody th")].map((th) => th.innerText),
// 			["Total", "Company", "xphone", "xpad", "individual"],
// 			"The row headers should be as expected"
// 		);

// 		// open groupby menu generator and add a new groupby
// 		await toggleSearchBarMenu();
// 		await contains(`.o_add_custom_group_menu`).select("bar");

// 		assert.deepEqual(
// 			[...target.querySelectorAll("thead th")].map((th) => th.innerText),
// 			["", "Total", "Foo"],
// 			"The col headers should be as expected"
// 		);
// 		assert.deepEqual(
// 			[...target.querySelectorAll("tbody th")].map((th) => th.innerText),
// 			["Total", "Company", "Yes", "individual", "No", "Yes"],
// 			"The row headers should be as expected"
// 		);
// 	}
// );

// test("display only one dropdown menu", async () => {
// 	expect.assertions(1);

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 			<pivot>
// 				<field name="foo" type="measure"/>
// 			</pivot>`,
// 	});

// 	// add a col groupby on Product
// 	await contains("thead th.o_pivot_header_cell_closed").click();
// 	await contains(".o-dropdown--menu .dropdown-item:eq(5)").click();

// 	// Click on the two header dropdown togglers
// 	await contains("thead th.o_pivot_header_cell_closed:eq(0)").click();
// 	await contains("thead th.o_pivot_header_cell_closed:eq(1)").click();

// 	assert.containsOnce(
// 		target,
// 		".o-dropdown--menu",
// 		"Only one dropdown should be displayed at a time"
// 	);
// });

// test("Server order is kept by default", async () => {
// 	expect.assertions(1);

// 	let isSecondReadGroup = false;
// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 			<pivot>
// 				<field name="customer" type="row"/>
// 				<field name="foo" type="measure"/>
// 			</pivot>`,
// 		mockRPC(route, args) {
// 			if (args.method === "read_group") {
// 				if (isSecondReadGroup) {
// 					return Promise.resolve([
// 						{
// 							customer: [2, "Second"],
// 							foo: 18,
// 							__count: 2,
// 							__domain: [["customer", "=", 2]],
// 						},
// 						{
// 							customer: [1, "First"],
// 							foo: 14,
// 							__count: 2,
// 							__domain: [["customer", "=", 1]],
// 						},
// 					]);
// 				}
// 				isSecondReadGroup = true;
// 			}
// 		},
// 	});

// 	const values = [
// 		"32", // Total Value
// 		"18", // Second
// 		"14", // First
// 	];
// 	expect(getCurrentValues()).toBe(values.join());
// });

// test("pivot rendering with boolean field", async () => {
// 	expect.assertions(4);

// 	serverData.models.partner.fields.bar = {
// 		string: "bar",
// 		type: "boolean",
// 		store: true,
// 		searchable: true,
// 		aggregator: "bool_or",
// 	};
// 	Partner._records =[
// 		{ id: 1, bar: true, date: "2019-12-14" },
// 		{ id: 2, bar: false, date: "2019-05-14" },
// 	];

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 			<pivot>
// 				<field name="date" type="row" interval="day"/>
// 				<field name="bar" type="col"/>
// 				<field name="bar" string="SLA status Failed" type="measure"/>
// 			</pivot>`,
// 	});

// 	expect($(target).find('tbody tr:contains("2019-12-14")').length).toBe(1);
// 	assert.ok(
// 		$(target).find('tbody tr:contains("2019-12-14") [type="checkbox"]').is(":checked"),
// 		"first column contains checkbox and value should be ticked"
// 	);
// 	expect($(target).find('tbody tr:contains("2019-05-14")').length).toBe(1);
// 	assert.notOk(
// 		$(target).find('tbody tr:contains("2019-05-14") [type="checkbox"]').is(":checked"),
// 		"second column should have checkbox that is not checked by default"
// 	);
// });

// test("empty pivot view with action helper", async () => {
// 	serverData.views = {
// 		"partner,false,pivot": `
// 			<pivot>
// 				<field name="product_id" type="measure"/>
// 				<field name="date" interval="month" type="col"/>
// 			</pivot>`,
// 		"partner,false,search": `
// 			<search>
// 				<filter name="small_than_0" string="Small Than 0" domain="[('id', '&lt;', 0)]"/>
// 			</search>`,
// 	};
// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		context: { search_default_small_than_0: true },
// 		noContentHelp: markup('<p class="abc">click to add a foo</p>'),
// 		config: {
// 			views: [[false, "search"]],
// 		},
// 	});

// 	expect(".o_view_nocontent .abc").toHaveCount(1);
// 	expect("table").toHaveCount(0);

// 	await removeFacet();

// 	expect(".o_view_nocontent .abc").toHaveCount(0);
// 	expect("table").toHaveCount(1);
// });

// test("empty pivot view with sample data", async () => {
// 	serverData.views = {
// 		"partner,false,pivot": `
// 			<pivot sample="1">
// 				<field name="product_id" type="measure"/>
// 				<field name="date" interval="month" type="col"/>
// 			</pivot>`,
// 		"partner,false,search": `
// 			<search>
// 				<filter name="small_than_0" string="Small Than 0" domain="[('id', '&lt;', 0)]"/>
// 			</search>`,
// 	};

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		context: { search_default_small_than_0: true },
// 		noContentHelp: markup('<p class="abc">click to add a foo</p>'),
// 		config: {
// 			views: [[false, "search"]],
// 		},
// 	});

// 	assert.hasClass(target.querySelector(".o_pivot_view .o_content"), "o_view_sample_data");
// 	expect(".o_view_nocontent .abc").toHaveCount(1);

// 	await removeFacet();

// 	assert.doesNotHaveClass(
// 		target.querySelector(".o_pivot_view .o_content"),
// 		"o_view_sample_data"
// 	);
// 	expect(".o_view_nocontent .abc").toHaveCount(0);
// 	expect("table").toHaveCount(1);
// });

// test("non empty pivot view with sample data", async () => {
// 	serverData.views = {
// 		"partner,false,pivot": `
// 			<pivot sample="1">
// 				<field name="product_id" type="measure"/>
// 				<field name="date" interval="month" type="col"/>
// 			</pivot>`,
// 		"partner,false,search": `
// 			<search>
// 				<filter name="small_than_0" string="Small Than 0" domain="[('id', '&lt;', 0)]"/>
// 			</search>`,
// 	};

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		noContentHelp: markup('<p class="abc">click to add a foo</p>'),
// 		config: {
// 			views: [[false, "search"]],
// 		},
// 	});

// 	assert.doesNotHaveClass(target, "o_view_sample_data");
// 	expect(".o_view_nocontent .abc").toHaveCount(0);
// 	expect("table").toHaveCount(1);

// 	await toggleSearchBarMenu();
// 	await toggleMenuItem("Small Than 0");

// 	assert.doesNotHaveClass(target, "o_view_sample_data");
// 	expect(".o_view_nocontent .abc").toHaveCount(1);
// 	expect("table").toHaveCount(0);
// });

// test("pivot is reloaded when leaving and coming back", async () => {
// 	serverData.views = {
// 		"partner,false,pivot": `
// 			<pivot>
// 				<field name="customer" type="row"/>
// 			</pivot>`,
// 		"partner,false,search": `<search/>`,
// 		"partner,false,list": '<tree><field name="foo"/></tree>',
// 	};

// 	const mockRPC = (route, args) => {
// 		assert.step(args.method || route);
// 	};
// 	const webClient = await createWebClient({  mockRPC });

// 	await doAction(webClient, {
// 		res_model: "partner",
// 		type: "ir.actions.act_window",
// 		views: [
// 			[false, "pivot"],
// 			[false, "list"],
// 		],
// 	});

// 	expect(".o_pivot_view").toHaveCount(1);
// 	expect(getCurrentValues()).toBe(["4", "2", "2"].join(","));

// 	assert.verifySteps(["/web/webclient/load_menus", "get_views", "read_group", "read_group"]);

// 	// switch to list view
// 	await contains(".o_control_panel .o_switch_view.o_list").click();

// 	expect(".o_list_view").toHaveCount(1);
// 	assert.verifySteps(["web_search_read"]);

// 	// switch back to pivot
// 	await contains(".o_control_panel .o_switch_view.o_pivot").click();

// 	expect(".o_pivot_view").toHaveCount(1);
// 	expect(getCurrentValues()).toBe(["4", "2", "2"].join(","));

// 	assert.verifySteps(["read_group", "read_group"]);
// });

// test("expanded groups are kept when leaving and coming back", async () => {
// 	serverData.views = {
// 		"partner,false,pivot": `
// 			<pivot>
// 				<field name="customer" type="row"/>
// 			</pivot>`,
// 		"partner,false,search": `<search/>`,
// 		"partner,false,list": '<tree><field name="foo"/></tree>',
// 	};

// 	const webClient = await createWebClient({ serverData });

// 	await doAction(webClient, {
// 		res_model: "partner",
// 		type: "ir.actions.act_window",
// 		views: [
// 			[false, "pivot"],
// 			[false, "list"],
// 		],
// 	});

// 	expect(".o_pivot_view").toHaveCount(1);
// 	expect(getCurrentValues()).toBe(["4", "2", "2"].join(","));

// 	// drill down first row group (group by company_type)
// 	await contains("tbody .o_pivot_header_cell_closed").click();
// 	await contains(".o-dropdown--menu .dropdown-item").click();

// 	expect(getCurrentValues()).toBe(["4", "2", "1", "1", "2"].join(","));

// 	// switch to list view
// 	await contains(".o_control_panel .o_switch_view.o_list").click();

// 	expect(".o_list_view").toHaveCount(1);

// 	// switch back to pivot
// 	await contains(".o_control_panel .o_switch_view.o_pivot").click();

// 	expect(".o_pivot_view").toHaveCount(1);
// 	expect(getCurrentValues()).toBe(["4", "2", "1", "1", "2"].join(","));
// });

// test("sorted rows are kept when leaving and coming back", async () => {
// 	serverData.views = {
// 		"partner,false,pivot": `
// 			<pivot>
// 				<field name="foo" type="measure"/>
// 				<field name="product_id" type="row"/>
// 			</pivot>`,
// 		"partner,false,search": `<search/>`,
// 		"partner,false,list": '<tree><field name="foo"/></tree>',
// 	};

// 	const webClient = await createWebClient({ serverData });

// 	await doAction(webClient, {
// 		res_model: "partner",
// 		type: "ir.actions.act_window",
// 		views: [
// 			[false, "pivot"],
// 			[false, "list"],
// 		],
// 	});

// 	expect(".o_pivot_view").toHaveCount(1);
// 	expect(getCurrentValues()).toBe(["32", "12", "20"].join(","));

// 	// sort the first group
// 	await contains("th.o_pivot_measure_row").click();
// 	await contains("th.o_pivot_measure_row").click();

// 	expect(getCurrentValues()).toBe(["32", "20", "12"].join(","));

// 	// switch to list view
// 	await contains(".o_control_panel .o_switch_view.o_list").click();

// 	expect(".o_list_view").toHaveCount(1);

// 	// switch back to pivot
// 	await contains(".o_control_panel .o_switch_view.o_pivot").click();

// 	expect(".o_pivot_view").toHaveCount(1);
// 	expect(getCurrentValues()).toBe(["32", "20", "12"].join(","));
// });

// test("correctly handle concurrent reloads", async () => {
// 	serverData.views = {
// 		"partner,false,pivot": `
// 			<pivot>
// 				<field name="foo" type="measure"/>
// 				<field name="product_id" type="row"/>
// 			</pivot>`,
// 		"partner,false,search": `<search/>`,
// 		"partner,false,list": '<tree><field name="foo"/></tree>',
// 	};

// 	let def;
// 	let readGroupCount = 0;
// 	const mockRPC = (route, args) => {
// 		if (args.method === "read_group" && def) {
// 			readGroupCount++;
// 			if (readGroupCount === 2) {
// 				// slow down last read_group of first reload
// 				return Promise.resolve(def);
// 			}
// 		}
// 	};
// 	const webClient = await createWebClient({  mockRPC });

// 	await doAction(webClient, {
// 		res_model: "partner",
// 		type: "ir.actions.act_window",
// 		views: [
// 			[false, "pivot"],
// 			[false, "list"], // s.t. there is a pivot view switcher
// 		],
// 	});

// 	expect(".o_pivot_view").toHaveCount(1);
// 	expect(getCurrentValues()).toBe(["32", "12", "20"].join(","));

// 	// drill down first row group (group by company_type)
// 	await contains("tbody .o_pivot_header_cell_closed").click();
// 	await contains(".o-dropdown--menu .dropdown-item").click();

// 	expect(getCurrentValues()).toBe(["32", "12", "12", "20"].join(","));

// 	// reload twice by clicking on pivot view switcher
// 	def = new Deferred();
// 	await contains(".o_control_panel .o_switch_view.o_pivot").click();
// 	await contains(".o_control_panel .o_switch_view.o_pivot").click();

// 	def.resolve();
// 	await animationFrame();

// 	expect(getCurrentValues()).toBe(["32", "12", "12", "20"].join(","));
// });

// test("consecutively toggle several measures", async () => {
// 	let def;
// 	serverData.models.partner.fields.foo2 = {
// 		...serverData.models.partner.fields.foo,
// 		string: "Foo2",
// 		store: true,
// 	};

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 			<pivot>
// 				<field name="foo" type="measure"/>
// 				<field name="product_id" type="row"/>
// 			</pivot>`,
// 		mockRPC(route, args) {
// 			if (args.method === "read_group") {
// 				return Promise.resolve(def);
// 			}
// 		},
// 	});

// 	expect(getCurrentValues()).toBe(["32", "12", "20"].join(","));

// 	// Toggle several measures (the reload is blocked, so all measures should be toggled in once)
// 	def = new Deferred();
// 	await toggleMenu(target, "Measures");
// 	await toggleMenuItem("Foo2"); // add foo2
// 	expect(getCurrentValues()).toBe(["32", "12", "20"].join(","));
// 	await toggleMenuItem("Foo"); // remove foo
// 	expect(getCurrentValues()).toBe(["32", "12", "20"].join(","));
// 	await toggleMenuItem("Count"); // add count
// 	expect(getCurrentValues()).toBe(["32", "12", "20"].join(","));

// 	def.resolve();
// 	await animationFrame();

// 	expect(getCurrentValues()).toBe(["0", "4", "0", "1", "0", "3"].join(","));
// });

// test("flip axis while loading a filter", async () => {
// 	let def;
// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 			<pivot>
// 				<field name="foo" type="measure"/>
// 				<field name="date" type="col"/>
// 				<field name="product_id" type="row"/>
// 			</pivot>`,
// 		searchViewArch: `
// 			<search>
// 				<filter name="my_filter" string="My Filter" domain="[('product_id', '=', 41)]"/>
// 			</search>`,
// 		mockRPC(route, args) {
// 			if (args.method === "read_group") {
// 				return Promise.resolve(def);
// 			}
// 		},
// 	});

// 	const values = ["2", "1", "29", "32", "12", "12", "2", "1", "17", "20"];
// 	expect(getCurrentValues()).toBe(values.join(","));

// 	// Set a domain (this reload is delayed)
// 	def = new Deferred();
// 	await toggleSearchBarMenu();
// 	await toggleMenuItem("My Filter");
// 	expect(getCurrentValues()).toBe(values.join(","));

// 	// Flip axis
// 	await contains(".o_pivot_flip_button").click();
// 	expect(getCurrentValues()).toBe(values.join(","));

// 	def.resolve();
// 	await animationFrame();

// 	expect(getCurrentValues()).toBe(["20", "2", "1", "17"].join(","));
// });

// test("sort rows while loading a filter", async () => {
// 	let def;
// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 			<pivot>
// 				<field name="foo" type="measure"/>
// 				<field name="product_id" type="row"/>
// 			</pivot>`,
// 		searchViewArch: `
// 			<search>
// 				<filter name="my_filter" string="My Filter" domain="[('product_id', '=', 41)]"/>
// 			</search>`,
// 		mockRPC(route, args) {
// 			if (args.method === "read_group") {
// 				return Promise.resolve(def);
// 			}
// 		},
// 	});

// 	expect(getCurrentValues()).toBe(["32", "12", "20"].join(","));

// 	// Set a domain (this reload is delayed)
// 	def = new Deferred();
// 	await toggleSearchBarMenu();
// 	await toggleMenuItem("My Filter");
// 	expect(getCurrentValues()).toBe(["32", "12", "20"].join(","));

// 	// Sort rows (this operation should be ignored as it concerns the old
// 	// table, which will be replaced soon)
// 	await contains("th.o_pivot_measure_row").click();
// 	expect(getCurrentValues()).toBe(["32", "12", "20"].join(","));

// 	def.resolve();
// 	await animationFrame();

// 	expect(getCurrentValues()).toBe(["20", "20"].join(","));
// });

// test("close a group while loading a filter", async () => {
// 	let def;
// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 			<pivot>
// 				<field name="foo" type="measure"/>
// 				<field name="product_id" type="row"/>
// 			</pivot>`,
// 		searchViewArch: `
// 			<search>
// 				<filter name="my_filter" string="My Filter" domain="[('product_id', '=', 41)]"/>
// 			</search>`,
// 		mockRPC(route, args) {
// 			if (args.method === "read_group") {
// 				return Promise.resolve(def);
// 			}
// 		},
// 	});

// 	expect(getCurrentValues()).toBe(["32", "12", "20"].join(","));

// 	// Set a domain (this reload is delayed)
// 	def = new Deferred();
// 	await toggleSearchBarMenu();
// 	await toggleMenuItem("My Filter");
// 	expect(getCurrentValues()).toBe(["32", "12", "20"].join(","));

// 	// Close a group (this operation should be ignored as it concerns the old
// 	// table, which will be replaced soon)
// 	await contains("tbody .o_pivot_header_cell_opened").click();
// 	expect(getCurrentValues()).toBe(["32", "12", "20"].join(","));

// 	def.resolve();
// 	await animationFrame();

// 	expect(getCurrentValues()).toBe(["20", "20"].join(","));
// });

// test("add a groupby while loading a filter", async () => {
// 	let def;
// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 			<pivot>
// 				<field name="foo" type="measure"/>
// 				<field name="product_id" type="row"/>
// 			</pivot>`,
// 		searchViewArch: `
// 			<search>
// 				<filter name="my_filter" string="My Filter" domain="[('product_id', '=', 41)]"/>
// 			</search>`,
// 		mockRPC(route, args) {
// 			if (args.method === "read_group") {
// 				return Promise.resolve(def);
// 			}
// 		},
// 	});

// 	expect(getCurrentValues()).toBe(["32", "12", "20"].join(","));

// 	// Set a domain (this reload is delayed)
// 	def = new Deferred();
// 	await toggleSearchBarMenu();
// 	await toggleMenuItem("My Filter");
// 	expect(getCurrentValues()).toBe(["32", "12", "20"].join(","));

// 	// Add a groupby (this operation should be ignored as it concerns the old
// 	// table, which will be replaced soon)
// 	await contains("thead .o_pivot_header_cell_closed").click();
// 	await contains(".o-dropdown--menu .dropdown-item").click();
// 	expect(getCurrentValues()).toBe(["32", "12", "20"].join(","));

// 	def.resolve();
// 	await animationFrame();

// 	expect(getCurrentValues()).toBe(["20", "20"].join(","));
// });

// test("expand a group while loading a filter", async () => {
// 	let def;
// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 			<pivot>
// 				<field name="foo" type="measure"/>
// 				<field name="product_id" type="row"/>
// 			</pivot>`,
// 		searchViewArch: `
// 			<search>
// 				<filter name="my_filter" string="My Filter" domain="[('product_id', '=', 41)]"/>
// 			</search>`,
// 		mockRPC(route, args) {
// 			if (args.method === "read_group") {
// 				return Promise.resolve(def);
// 			}
// 		},
// 	});

// 	// Add a groupby, to have a group to expand afterwards
// 	await contains("tbody .o_pivot_header_cell_closed").click();
// 	await contains(".o-dropdown--menu .dropdown-item").click();

// 	expect(getCurrentValues()).toBe(["32", "12", "12", "20"].join(","));

// 	// Set a domain (this reload is delayed)
// 	def = new Deferred();
// 	await toggleSearchBarMenu();
// 	await toggleMenuItem("My Filter");
// 	expect(getCurrentValues()).toBe(["32", "12", "12", "20"].join(","));

// 	// Expand a group (this operation should be ignored as it concerns the old
// 	// table, which will be replaced soon)
// 	await contains("tbody .o_pivot_header_cell_closed:eq(1)").click();
// 	expect(getCurrentValues()).toBe(["32", "12", "12", "20"].join(","));

// 	def.resolve();
// 	await animationFrame();

// 	expect(getCurrentValues()).toBe(["20", "20"].join(","));
// });

// test(
// 	"concurrent reloads: add a filter, and directly toggle a measure",
// 	async function (assert) {
// 		let def;
// 		await mountView({
// 			type: "pivot",
// 			resModel: "partner",
			
// 			arch: `
// 				<pivot>
// 					<field name="foo" type="measure"/>
// 					<field name="product_id" type="row"/>
// 				</pivot>`,
// 			searchViewArch: `
// 				<search>
// 					<filter name="my_filter" string="My Filter" domain="[('product_id', '=', 37)]"/>
// 				</search>`,
// 			mockRPC(route, args) {
// 				if (args.method === "read_group") {
// 					return Promise.resolve(def);
// 				}
// 			},
// 		});

// 		expect(getCurrentValues()).toBe(["32", "12", "20"].join(","));

// 		// Set a domain (this reload is delayed)
// 		def = new Deferred();
// 		await toggleSearchBarMenu();
// 		await toggleMenuItem("My Filter");

// 		expect(getCurrentValues()).toBe(["32", "12", "20"].join(","));

// 		// Toggle a measure
// 		await toggleMenu(target, "Measures");
// 		await toggleMenuItem("Count");

// 		expect(getCurrentValues()).toBe(["32", "12", "20"].join(","));

// 		def.resolve();
// 		await animationFrame();

// 		expect(getCurrentValues()).toBe(["12", "1", "12", "1"].join(","));
// 	}
// );

// test(
// 	"if no measure is set in arch, 'Count' is used as measure initially",
// 	async function (assert) {
// 		await mountView({
// 			type: "pivot",
// 			resModel: "partner",
			
// 			arch: `<pivot/>`,
// 		});

// 		assert.deepEqual(
// 			[...target.querySelectorAll("thead th")].map((e) => e.innerText),
// 			["", "Total", "Count"]
// 		);
// 	}
// );

// test(
// 	"if (at least) one measure is set in arch and display_quantity is false or unset, 'Count' is not used as measure initially",
// 	async function (assert) {
// 		await mountView({
// 			type: "pivot",
// 			resModel: "partner",
			
// 			arch: `
// 			<pivot>
// 				<field name="foo" type="measure"/>
// 			</pivot>
// 		`,
// 		});

// 		assert.deepEqual(
// 			[...target.querySelectorAll("thead th")].map((e) => e.innerText),
// 			["", "Total", "Foo"]
// 		);
// 	}
// );

// test(
// 	"if (at least) one measure is set in arch and display_quantity is true, 'Count' is used as measure initially",
// 	async function (assert) {
// 		await mountView({
// 			type: "pivot",
// 			resModel: "partner",
			
// 			arch: `
// 			<pivot display_quantity="1">
// 				<field name="foo" type="measure"/>
// 			</pivot>
// 		`,
// 		});

// 		assert.deepEqual(
// 			[...target.querySelectorAll("thead th")].map((e) => e.innerText),
// 			["", "Total", "Count", "Foo"]
// 		);
// 	}
// );

// test("'Measures' menu when there is no measurable fields", async () => {
// 	serverData.models.partner = {
// 		fields: {},
// 		records: [{ id: 1, display_name: "The one" }],
// 	};
// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `<pivot/>`,
// 	});

// 	await toggleMenu(target, "Measures");

// 	// "Count" is the only measure available
// 	assert.deepEqual(
// 		[...target.querySelectorAll(".o-dropdown--menu .o_menu_item")].map((e) => e.innerText),
// 		["Count"]
// 	);
// 	// No separator should be displayed in the menu "Measures"
// 	expect(".o-dropdown--menu div.dropdown-divider").toHaveCount(0);
// });

// QUnit.skip(
// 	"comparison with two groupbys: rows from reference period should be displayed",
// 	async function (assert) {
// 		patchDate(2023, 2, 22, 1, 0, 0);
// 		expect.assertions(3);

// 		Partner._records =[
// 			{ id: 1, date: "2021-10-10", product_id: 1, customer: 1 },
// 			{ id: 2, date: "2020-10-10", product_id: 2, customer: 1 },
// 		];
// 		serverData.models.product.records = [
// 			{ id: 1, display_name: "A" },
// 			{ id: 2, display_name: "B" },
// 		];
// 		serverData.models.customer.records = [{ id: 1, display_name: "P" }];

// 		await mountView({
// 			type: "pivot",
// 			resModel: "partner",
			
// 			arch: `
// 			<pivot>
// 				<field name="customer" type="row"/>
// 				<field name="product_id" type="row"/>
// 			</pivot>
// 		`,
// 			searchViewArch: `
// 			<search>
// 				<filter name='date' date='date'/>
// 			</search>
// 		`,
// 		});

// 		// compare 2021 to 2020
// 		await toggleSearchBarMenu();
// 		await toggleMenuItem("Date");
// 		await toggleMenuItemOption("Date", "2021");
// 		await toggleMenuItem(target.querySelector(".o_comparison_menu"), 0);

// 		assert.deepEqual(
// 			[...target.querySelectorAll("th")].slice(0, 6).map((el) => el.innerText),
// 			["", "Total", "Count", "2020", "2021", "Variation"],
// 			"The col headers should be as expected"
// 		);

// 		assert.deepEqual(
// 			[...target.querySelectorAll("th")].slice(6).map((el) => el.innerText),
// 			["Total", "P", "B", "A"],
// 			"The row headers should be as expected"
// 		);

// 		const values = ["1", "1", "0%", "1", "1", "0%", "1", "0", "-100%", "0", "1", "100%"];
// 		expect(getCurrentValues()).toBe(values.join());
// 	}
// );

// test("pivot_row_groupby should be also used after first load", async () => {
// 	const ids = [1, 2];
// 	const expectedContexts = [
// 		{
// 			group_by: ["bar"],
// 			pivot_column_groupby: [],
// 			pivot_measures: ["__count"],
// 			pivot_row_groupby: ["product_id"],
// 		},
// 		{
// 			group_by: ["bar", "customer"],
// 			pivot_column_groupby: [],
// 			pivot_measures: ["__count"],
// 			pivot_row_groupby: ["customer"],
// 		},
// 	];

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `<pivot/>`,
// 		searchViewArch: `
// 			<search>
// 				<filter name='product_id' string="Product" context="{'group_by':'product_id'}"/>
// 				<filter name='customer' string="Customer" context="{'group_by':'customer'}"/>
// 			</search>
// 		`,
// 		groupBy: ["bar"],
// 		mockRPC(route, args) {
// 			if (args.method === "create_or_replace") {
// 				assert.deepEqual(args.args[0].context, expectedContexts.shift());
// 				return ids.shift();
// 			}
// 		},
// 	});

// 	assert.deepEqual(
// 		[...target.querySelectorAll("th")].slice(3).map((el) => el.innerText),
// 		["Total", "No", "Yes"],
// 		"The row headers should be as expected"
// 	);

// 	await contains("tbody th").click(); // click on row header "Total"
// 	await contains("tbody th").click(); // click on row header "Total"
// 	await contains(".o-dropdown--menu .o_menu_item").click(); // select "Product"

// 	assert.deepEqual(
// 		[...target.querySelectorAll("th")].slice(3).map((el) => el.innerText),
// 		["Total", "xphone", "xpad"],
// 		"The row headers should be as expected"
// 	);

// 	await toggleSearchBarMenu();
// 	await toggleSaveFavorite(target);
// 	await editFavoriteName(target, "Favorite");
// 	await saveFavorite(target);

// 	assert.deepEqual(
// 		[...target.querySelectorAll("th")].slice(3).map((el) => el.innerText),
// 		["Total", "xphone", "xpad"],
// 		"The row headers should be as expected"
// 	);

// 	await removeFacet();

// 	assert.deepEqual(
// 		[...target.querySelectorAll("th")].slice(3).map((el) => el.innerText),
// 		["Total", "No", "Yes"],
// 		"The row headers should be as expected"
// 	);

// 	await toggleSearchBarMenu();
// 	await toggleMenuItem("Favorite");

// 	assert.deepEqual(
// 		[...target.querySelectorAll("th")].slice(3).map((el) => el.innerText),
// 		["Total", "xphone", "xpad"],
// 		"The row headers should be as expected"
// 	);

// 	await toggleMenuItem("customer");

// 	assert.deepEqual(
// 		[...target.querySelectorAll("th")].slice(3).map((el) => el.innerText),
// 		["Total", "xphone", "First", "xpad", "First", "Second"],
// 		"The row headers should be as expected"
// 	);

// 	await contains("tbody th").click(); // click on row header "Total"
// 	await contains("tbody th").click(); // click on row header "Total"
// 	await contains(".o-dropdown--menu .o_menu_item:eq(1)").click(); // select "Customer"

// 	assert.deepEqual(
// 		[...target.querySelectorAll("th")].slice(3).map((el) => el.innerText),
// 		["Total", "First", "Second"],
// 		"The row headers should be as expected"
// 	);

// 	await toggleSearchBarMenu();
// 	await toggleSaveFavorite(target);
// 	await editFavoriteName(target, "Favorite 2");
// 	await saveFavorite(target);

// 	assert.deepEqual(
// 		[...target.querySelectorAll("th")].slice(3).map((el) => el.innerText),
// 		["Total", "First", "Second"],
// 		"The row headers should be as expected"
// 	);
// });

// test(
// 	"pivot_row_groupby should be also used after first load (2)",
// 	async function (assert) {
// 		await mountView({
			
// 			type: "pivot",
// 			resModel: "partner",
// 			groupBy: ["product_id"],
// 			arch: `<pivot/>`,
// 			irFilters: [
// 				{
// 					user_id: [2, "Mitchell Admin"],
// 					name: "Favorite",
// 					id: 1,
// 					context: `
// 						{
// 							"group_by": [],
// 							"pivot_row_groupby": ["customer"],
// 							"pivot_col_groupby": [],
// 							"pivot_measures": ["foo"],
// 						}
// 					`,
// 					sort: "[]",
// 					domain: "",
// 					is_default: false,
// 					model_id: "foo",
// 					action_id: false,
// 				},
// 			],
// 		});

// 		assert.deepEqual(
// 			[...target.querySelectorAll("th")].slice(3).map((el) => el.innerText),
// 			["Total", "xphone", "xpad"],
// 			"The row headers should be as expected"
// 		);

// 		await toggleSearchBarMenu();
// 		await toggleMenuItem("Favorite");

// 		assert.deepEqual(
// 			[...target.querySelectorAll("th")].slice(3).map((el) => el.innerText),
// 			["Total", "First", "Second"],
// 			"The row headers should be as expected"
// 		);
// 	}
// );

// test(
// 	"specific pivot keys in action context must have less importance than in favorite context",
// 	async function (assert) {
// 		await mountView({
// 			type: "pivot",
// 			resModel: "partner",
			
// 			arch: `<pivot/>`,
// 			context: {
// 				pivot_column_groupby: [],
// 				pivot_measures: ["__count"],
// 				pivot_row_groupby: [],
// 			},
// 			irFilters: [
// 				{
// 					user_id: [2, "Mitchell Admin"],
// 					name: "My favorite",
// 					id: 1,
// 					context: `{
// 						"pivot_column_groupby": ["bar"],
// 						"pivot_measures": ["computed_field"],
// 						"pivot_row_groupby": [],
// 					}`,
// 					sort: "[]",
// 					domain: "",
// 					is_default: true,
// 					model_id: "partner",
// 					action_id: false,
// 				},
// 				{
// 					user_id: [2, "Mitchell Admin"],
// 					name: "My favorite 2",
// 					id: 2,
// 					context: `{
// 						"pivot_column_groupby": ["product_id"],
// 						"pivot_measures": ["computed_field", "__count"],
// 						"pivot_row_groupby": [],
// 					}`,
// 					sort: "[]",
// 					domain: "",
// 					is_default: false,
// 					model_id: "partner",
// 					action_id: false,
// 				},
// 			],
// 		});

// 		assert.deepEqual(
// 			[...target.querySelectorAll("th")].slice(1, 6).map((el) => el.innerText),
// 			["Total", "", "No", "Yes", "Computed and not stored"]
// 		);

// 		await toggleSearchBarMenu();
// 		await toggleMenuItem("My favorite 2");

// 		assert.deepEqual(
// 			[...target.querySelectorAll("th")].slice(1, 11).map((el) => el.innerText),
// 			[
// 				"Total",
// 				"",
// 				"xphone",
// 				"xpad",
// 				"Computed and not stored",
// 				"Count",
// 				"Computed and not stored",
// 				"Count",
// 				"Computed and not stored",
// 				"Count",
// 			]
// 		);
// 	}
// );

// test(
// 	"favorite pivot_measures should be used even if found also in global context",
// 	async function (assert) {
// 		serverData.models.partner.fields.computed_field.store = true; // --> Computed and not stored displayed in "Measures" menu

// 		await mountView({
// 			type: "pivot",
// 			resModel: "partner",
			
// 			arch: `<pivot/>`,
// 			context: {
// 				pivot_measures: ["__count"],
// 			},
// 			mockRPC(route, args) {
// 				if (args.method === "create_or_replace") {
// 					assert.deepEqual(args.args[0].context, {
// 						group_by: [],
// 						pivot_column_groupby: [],
// 						pivot_measures: ["computed_field"],
// 						pivot_row_groupby: [],
// 					});
// 					return 1;
// 				}
// 			},
// 		});

// 		assert.deepEqual(
// 			[...target.querySelectorAll("th")].slice(1, 3).map((el) => el.innerText),
// 			["Total", "Count"]
// 		);

// 		await toggleMenu(target, "Measures");
// 		await toggleMenuItem("Count");
// 		await toggleMenuItem("Computed and not stored");

// 		assert.deepEqual(getFacetTexts(target), []);
// 		assert.deepEqual(
// 			[...target.querySelectorAll("th")].slice(1, 3).map((el) => el.innerText),
// 			["Total", "Computed and not stored"]
// 		);

// 		await toggleSearchBarMenu();
// 		await toggleSaveFavorite(target);
// 		await editFavoriteName(target, "Favorite");
// 		await saveFavorite(target);

// 		assert.deepEqual(getFacetTexts(target), ["Favorite"]);
// 		assert.deepEqual(
// 			[...target.querySelectorAll("th")].slice(1, 3).map((el) => el.innerText),
// 			["Total", "Computed and not stored"]
// 		);
// 	}
// );

// test("filter -> sort -> unfilter should not crash", async () => {
// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 				<pivot>
// 					<field name="product_id" type="row"/>
// 					<field name="bar" type="row"/>
// 				</pivot>
// 			`,
// 		searchViewArch: `
// 			<search>
// 				<filter name="xphone" domain="[('product_id', '=', 37)]" />
// 			</search>
// 		`,
// 		context: {
// 			search_default_xphone: true,
// 		},
// 	});

// 	assert.deepEqual(getFacetTexts(target), ["xphone"]);
// 	assert.deepEqual(
// 		[...target.querySelectorAll("tbody th")].map((el) => el.innerText),
// 		["Total", "xphone", "Yes"]
// 	);
// 	expect(getCurrentValues()).toBe(["1", "1", "1"].join());

// 	await contains(".o_pivot_measure_row").click();
// 	await toggleSearchBarMenu();
// 	await toggleMenuItem("xphone");

// 	assert.deepEqual(getFacetTexts(target), []);
// 	assert.deepEqual(
// 		[...target.querySelectorAll("tbody th")].map((el) => el.innerText),
// 		["Total", "xphone", "Yes", "xpad"]
// 	);
// 	expect(getCurrentValues()).toBe(["4", "1", "1", "3"].join());
// });

// test(
// 	"no class 'o_view_sample_data' when real data are presented",
// 	async function (assert) {
// 		serverData.models.partner.fields.foo.store = true;
// 		Partner._records =[];
// 		await mountView({
// 			type: "pivot",
// 			resModel: "partner",
			
// 			arch: `
// 				<pivot sample="1">
// 					<field name="product_id" type="row"/>
// 				</pivot>
// 			`,
// 		});

// 		expect(".o_pivot_view .o_view_sample_data").toHaveCount(1);
// 		expect(".o_pivot_view table").toHaveCount(1);
// 		await toggleMenu(target, "Measures");
// 		await toggleMenuItem("Foo");
// 		expect(".o_pivot_view .o_view_sample_data").toHaveCount(0);
// 		expect(".o_pivot_view table").toHaveCount(0);
// 	}
// );

// test("group by properties in pivot view", async () => {
// 	expect.assertions(18);

// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: "<pivot/>",
// 		searchViewArch: `
// 			<search>
// 				<filter name='group_by_properties' string="Properties" context="{'group_by':'properties'}"/>
// 			</search>
// 		`,
// 		mockRPC(route, args) {
// 			if (
// 				route === "/web/dataset/call_kw/partner/web_search_read" &&
// 				args.kwargs.specification?.properties_definition
// 			) {
// 				assert.step("fetch_definition");
// 			} else if (
// 				route === "/web/dataset/call_kw/partner/read_group" &&
// 				args.kwargs.groupby?.includes("properties.my_char")
// 			) {
// 				assert.step("read_group");
// 				return [
// 					{
// 						"properties.my_char": false,
// 						__domain: [["properties.my_char", "=", false]],
// 						__count: 2,
// 					},
// 					{
// 						"properties.my_char": "aaa",
// 						__domain: [["properties.my_char", "=", "aaa"]],
// 						__count: 1,
// 					},
// 					{
// 						"properties.my_char": "bbb",
// 						__domain: [["properties.my_char", "=", "bbb"]],
// 						__count: 1,
// 					},
// 				];
// 			}
// 		},
// 	});

// 	expect(target.querySelectorAll(".o_value").length).toBe(1);
// 	expect(target.querySelector(".o_value").innerText).toBe("4");

// 	await contains(".border-top-0 span").click();
// 	assert.verifySteps([]);

// 	const propertiesItem = target.querySelector(".o_accordion_toggle");
// 	assert.ok(propertiesItem);
// 	expect(propertiesItem.innerText).toBe("Properties");
// 	await contains("propertiesItem").click();

// 	await animationFrame();
// 	assert.verifySteps(["fetch_definition"]);

// 	await contains(".o_accordion_values .o_menu_item").click();

// 	await animationFrame();
// 	assert.verifySteps(["read_group"]);

// 	const cells = target.querySelectorAll(".o_value");
// 	expect(cells.length).toBe(4);
// 	expect(cells[0].innerText).toBe("2");
// 	expect(cells[1].innerText).toBe("1");
// 	expect(cells[2].innerText).toBe("1");
// 	expect(cells[3].innerText).toBe("4");

// 	const columns = target.querySelectorAll(".o_pivot_header_cell_closed");
// 	expect(columns.length).toBe(4);
// 	expect(columns[0].innerText).toBe("None");
// 	expect(columns[1].innerText).toBe("aaa");
// 	expect(columns[2].innerText).toBe("bbb");
// });

// test("avoid duplicates in read_group parameter 'groupby'", async () => {
// 	await mountView({
// 		type: "pivot",
// 		resModel: "partner",
		
// 		arch: `
// 				<pivot sample="1">
// 					<field name="date" type="row"/>
// 					<field name="date" type="col" interval="month"/>
// 				</pivot>
// 			`,
// 		mockRPC(_, { method, kwargs }) {
// 			if (method === "read_group") {
// 				assert.step(JSON.stringify(kwargs.groupby));
// 			}
// 		},
// 	});
// 	assert.verifySteps([`[]`, `["date:month"]`]);
// });

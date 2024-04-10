import { describe, expect, test } from "@odoo/hoot";
import { queryAllTexts } from "@odoo/hoot-dom";
import { animationFrame } from "@odoo/hoot-mock";
import { Component, xml } from "@odoo/owl";
import { contains, defineModels, fields, models } from "@web/../tests/web_test_helpers";
import { mountWithSearch } from "./helpers";

import { SearchPanel } from "@web/search/search_panel/search_panel";

class Partner extends models.Model {
    name = fields.Char();
    foo = fields.Char();
    bar = fields.Boolean();
    int_field = fields.Integer({ string: "Int Field", aggregator: "sum" });
    company_id = fields.Many2one({ string: "res.company", relation: "res.company" });
    company_ids = fields.Many2many({ string: "Companies", relation: "res.company" });
    category_id = fields.Many2one({ string: "category", relation: "category" });
    state = fields.Selection({
        selection: [
            ["abc", "ABC"],
            ["def", "DEF"],
            ["ghi", "GHI"],
        ],
    });

    _records = [
        {
            id: 1,
            bar: true,
            foo: "yop",
            int_field: 1,
            company_ids: [3],
            company_id: 3,
            state: "abc",
            category_id: 6,
        },
        {
            id: 2,
            bar: true,
            foo: "blip",
            int_field: 2,
            company_ids: [3],
            company_id: 5,
            state: "def",
            category_id: 7,
        },
        {
            id: 3,
            bar: true,
            foo: "gnap",
            int_field: 4,
            company_ids: [],
            company_id: 3,
            state: "ghi",
            category_id: 7,
        },
        {
            id: 4,
            bar: false,
            foo: "blip",
            int_field: 8,
            company_ids: [5],
            company_id: 5,
            state: "ghi",
            category_id: 7,
        },
    ];
    _views = {
        search: /* xml */ `
            <search>
                <filter name="false_domain" string="False Domain" domain="[(0, '=', 1)]"/>
                <filter name="filter" string="Filter" domain="[('bar', '=', true)]"/>
                <filter name="true_domain" string="True Domain" domain="[(1, '=', 1)]"/>
                <filter name="group_by_bar" string="Bar" context="{ 'group_by': 'bar' }"/>
                <searchpanel view_types="kanban,list,toy">
                    <field name="company_id" enable_counters="1" expand="1"/>
                    <field name="category_id" select="multi" enable_counters="1" expand="1"/>
                </searchpanel>
            </search>
        `,
    };
}

class Company extends models.Model {
    _name = "res.company";

    name = fields.Char();
    parent_id = fields.Many2one({ string: "Parent company", relation: "res.company" });
    category_id = fields.Many2one({ string: "Category", relation: "category" });

    _records = [
        { id: 3, name: "asustek", category_id: 6 },
        { id: 5, name: "agrolait", category_id: 7 },
    ];
}

class Category extends models.Model {
    name = fields.Char({ string: "Category Name" });

    _records = [
        { id: 6, name: "gold" },
        { id: 7, name: "silver" },
    ];
}

defineModels([Partner, Company, Category]);

describe.current.tags("mobile");

test("basic search panel rendering", async () => {
    class Parent extends Component {
        static components = { SearchPanel };
        static template = xml`<SearchPanel/>`;
        static props = ["*"];
    }

    await mountWithSearch(Parent, {
        resModel: "partner",
        searchViewId: false,
    });

    expect(".o_search_panel .o-dropdown").toHaveCount(1);
    expect(".o_search_panel .o-dropdown").toHaveText("Category");

    await contains(".o_search_panel .o-dropdown").click();
    expect(".o_search_panel_section.o_search_panel_category").toHaveCount(1);
    expect(".o_search_panel_category_value").toHaveCount(3);
    expect(queryAllTexts(".o_search_panel_field li")).toEqual(["All", "gold", "silver"]);

    await contains(".o_search_panel_category_value:nth-of-type(2) header").click();
    expect(".o_search_panel .o-dropdown").toHaveText("gold");
    expect(".o_search_panel .o-dropdown .fa-circle").toHaveCount(1);
    expect(".o_search_panel a").toHaveCount(1);

    await contains(".o_search_panel a").click();
    expect(".o_search_panel .o-dropdown").toHaveText("Category");
    expect(".o_search_panel .o-dropdown .fa-circle").toHaveCount(0);
});

test("dropdown closes on item selection", async () => {
    class Parent extends Component {
        static components = { SearchPanel };
        static template = xml`<SearchPanel/>`;
        static props = ["*"];
    }

    await mountWithSearch(Parent, {
        resModel: "partner",
        searchViewId: false,
    });

    await contains(".o_search_panel .o-dropdown").click();
    expect(".o-dropdown--menu").toHaveCount(1);
    await contains(".o_search_panel_field :nth-child(2)").click();
    await animationFrame();

    expect(".o-dropdown--menu").toHaveCount(0);
});

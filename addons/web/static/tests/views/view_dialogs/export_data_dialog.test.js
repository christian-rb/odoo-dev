import { expect, test } from "@odoo/hoot";
import { click } from "@odoo/hoot-dom";
import { animationFrame } from "@odoo/hoot-mock";
import {
    contains,
    defineModels,
    fields,
    models,
    mountView,
    onRpc,
} from "@web/../tests/web_test_helpers";

/*async function exportAllAction(target) {
    click(".o_cp_action_menus .dropdown-toggle");
    click(".o-dropdown--menu .dropdown-item");
}


const clickExportMenuAction = async () => {
    click(".dropdown-menu span:contains(Export)");
    await animationFrame();
};*/

const openExportDataDialog = async () => {
    click(".o_list_record_selector input[type='checkbox']");
    await animationFrame();
    await contains(".o_control_panel .o_cp_action_menus .dropdown-toggle").click();
    await contains(".dropdown-menu span:contains(Export)").click();
    await animationFrame();
};

class Partner extends models.Model {
    display_name = fields.Char();
    foo = fields.Char();
    bar = fields.Boolean();

    _records = [
        { id: 1, foo: "blip", display_name: "blipblip", bar: true },
        { id: 2, foo: "ta tata ta ta", display_name: "macgyver", bar: false },
        { id: 3, foo: "piou piou", display_name: "Jack O'Neill", bar: true },
    ];
}
class Users extends models.Model {
    _name = "res.users";
    has_group() {
        return true;
    }
}
class IrExports extends models.Model {
    _name = "ir.exports";
    name = fields.Char();
    resource = fields.Char();
    export_fields = fields.One2many({ relation: "ir.exports.line" });
}
class IrExportsLine extends models.Model {
    _name = "ir.exports.line";
    name = fields.Char();
    export_id = fields.Many2one({ relation: "ir.exports" });
}
defineModels([Partner, Users, IrExports, IrExportsLine]);

const fetchedFields = {
    root: [
        {
            field_type: "one2many",
            string: "Activities",
            required: false,
            value: "activity_ids/id",
            id: "activity_ids",
            params: {
                model: "mail.activity",
                prefix: "activity_ids",
                name: "Activities",
            },
            relation_field: "res_id",
            children: true,
        },
        {
            children: false,
            field_type: "char",
            id: "foo",
            relation_field: null,
            required: true,
            string: "Foo",
            value: "foo",
        },
        {
            children: false,
            field_type: "boolean",
            id: "bar",
            relation_field: null,
            required: false,
            string: "Bar",
            value: "bar",
        },
    ],
    activity_ids: [
        {
            field_type: "one2many",
            string: "Attendants",
            required: false,
            value: "activity_ids/id",
            id: "activity_ids/partner_ids",
            params: {
                model: "mail.activity",
                prefix: "partner_ids",
                name: "Company",
            },
            children: true,
        },
        {
            field_type: "one2many",
            string: "Activity types",
            required: false,
            value: "activity_ids/id",
            id: "activity_ids/types",
            params: {
                model: "mail.activity",
                prefix: "activity_types",
                name: "Activity types",
            },
            children: true,
        },
        {
            id: "activity_ids/mail_template_ids",
            string: "Activities/Email templates",
            value: "activity_ids/mail_template_ids/id",
            children: true,
            field_type: "many2many",
            required: false,
            relation_field: null,
            default_export: false,
            params: {
                model: "mail.template",
                prefix: "activity_ids/mail_template_ids",
                name: "Activities/Email templates",
            },
        },
    ],
    partner_ids: [
        {
            children: false,
            field_type: "many2one",
            id: "activity_ids/partner_ids/company_ids",
            relation_field: null,
            string: "Company",
            value: "company_ids",
        },
        {
            children: false,
            field_type: "char",
            id: "activity_ids/partner_ids/name",
            relation_field: null,
            string: "Partner name",
            value: "partner_name",
        },
    ],
};

test("Export dialog UI test", async () => {
    onRpc("/web/export/formats", () => {
        return Promise.resolve([
            { tag: "csv", label: "CSV" },
            { tag: "xls", label: "Excel" },
        ]);
    });
    onRpc("/web/export/get_fields", () => {
        return Promise.resolve(fetchedFields.root);
    });

    await mountView({
        type: "list",
        resModel: "partner",
        arch: `<tree><field name="foo"/></tree>`,
        loadActionMenus: true,
    });

    await openExportDataDialog();
    expect(`.o_dialog`).toHaveCount(1);
    expect(`.o_dialog .o_export_tree_item`, {
        message: "There should be only three items visible",
    }).toHaveCount(3);
    await contains(".modal .o_export_search_input").edit("ac");
    expect(`.modal .o_export_tree_item`, {
        message: "Only matching item is visible",
    }).toHaveCount(1);
    click(".modal .o_export_tree_item .o_add_field");
    await animationFrame();
    expect(`.modal .o_export_field`, {
        message: "There should be two fields in export field list",
    }).toHaveCount(2);
    expect(".modal .o_export_field:nth-child(2)").toHaveText("Activities");
    expect(".o_export_search_input", {
        message: "Search input still contains the search string",
    }).toHaveValue("ac");
    await contains(".modal .o_export_search_input").edit("");
    expect(".modal .o_export_tree_item:nth-child(2) .o_tree_column").toHaveClass("fw-bolder");
    click(".modal .o_export_field:first-child .o_remove_field");
    await animationFrame();
    expect(`.modal .o_export_field`).toHaveCount(1);
});

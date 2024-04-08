/** @odoo-module **/

import {
    addFakeModel,
    addModelNamesToFetch,
    insertModelFields,
} from "@bus/../tests/helpers/model_definitions_helpers";

addModelNamesToFetch(["hr.employee", "hr.employee.public", "hr.department"]);

addFakeModel("m2x.avatar.employee", {
    employee_id: { string: "Employee", type: "many2one", relation: "hr.employee.public" },
    employee_ids: { string: "Employees", type: "many2many", relation: "hr.employee.public" },
});

insertModelFields("res.user", {
    name_work_location_display: { string: "Work Location", type: "char" },
    type_work_location: { string: "Work Location Type", type: "selection" },
});

/* @odoo-module */

import { patch } from "@web/core/utils/patch";
import { AvatarCardPopover } from "@mail/discuss/web/avatar_card/avatar_card_popover";
import { useService } from "@web/core/utils/hooks";

export const patchAvatarCardPopover = {
    setup() {
        super.setup();
        this.userInfoTemplate = "hr.avatarCardUserInfos";
        this.actionService = useService("action");
    },
    get fieldNames() {
        const fields = super.fieldNames;
        return fields.concat([
            "work_phone",
            "work_email",
            "name_work_location_display",
            "type_work_location",
            "job_title",
            "department_id",
            "employee_ids",
        ]);
    },
    get email() {
        return this.user.work_email || this.user.email;
    },
    get phone() {
        return this.user.work_phone || this.user.phone;
    },
    get locationIcon() {
        switch (this.user.type_work_location) {
            case "office":
                return "fa fa-fw fa-building-o";
            case "home":
                return "fa fa-fw fa-home";
            default:
                return "fa fa-fw fa-map-marker";
        }
    },
    async onClickViewEmployee() {
        const employeeId = this.user.employee_ids[0];
        const action = await this.orm.call("hr.employee", "get_formview_action", [employeeId]);
        this.actionService.doAction(action);
    },
};

export const unpatchAvatarCardPopover = patch(AvatarCardPopover.prototype, patchAvatarCardPopover);

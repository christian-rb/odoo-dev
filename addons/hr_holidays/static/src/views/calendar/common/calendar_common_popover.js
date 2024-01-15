/** @odoo-module */

import { CalendarCommonPopover } from "@web/views/calendar/calendar_common/calendar_common_popover";
import { onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { useResponsibleForApproval } from "@hr_holidays/views/hooks";

export class TimeOffCalendarCommonPopover extends CalendarCommonPopover {
    static subTemplates = {
        ...CalendarCommonPopover.subTemplates,
        footer: "hr_holidays.TimeOffCalendarCommonPopover.footer",
    };

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.viewType = "calendar";
        onWillStart(async () => {
            this.state = this.props?.record?.rawRecord?.state;
            this.isManager = await useResponsibleForApproval(this.props?.record?.rawRecord);
        });
    }

    get isEventDeletable() {
        return this.props.record.rawRecord.can_cancel || this.state && !['validate', 'refuse', 'cancel'].includes(this.state);
    }

    get isEventEditable() {
        return this.state !== undefined;
    }

    async onClickButton(ev) {
        const record = this.props.record.rawRecord;
        const args = (ev.target.name === "action_approve") ? [record.id, false] : [record.id];
        await this.orm.call("hr.leave", ev.target.name, args);
        await this.props.model.fetchRecords(this.props.model.data);
        await this.props.model.load();
        this.props.close();
    }
}

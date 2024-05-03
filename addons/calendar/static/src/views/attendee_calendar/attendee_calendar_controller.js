/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { CalendarController } from "@web/views/calendar/calendar_controller";
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";
import { onWillStart } from "@odoo/owl";
import { CalendarQuickCreate } from "@calendar/views/calendar_form/calendar_quick_create";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

export class AttendeeCalendarController extends CalendarController {
    static template = "calendar.AttendeeCalendarController";
    static components = {
        ...AttendeeCalendarController.components,
        QuickCreateFormView: CalendarQuickCreate,
    };

    setup() {
        super.setup();
        this.actionService = useService("action");
        this.orm = useService("orm");
        onWillStart(async () => {
            this.isSystemUser = await user.hasGroup("base.group_system");
        });
    }

    onClickAddButton() {
        this.actionService.doAction(
            {
                type: "ir.actions.act_window",
                res_model: "calendar.event",
                views: [[false, "form"]],
            },
            {
                additionalContext: this.props.context,
            }
        );
    }

    onSyncUnpause() {
        if (this.isSystemUser) {
            this.env.services.action.doAction("calendar.calendar_settings_action");
        } else {
            this.dialog.add(AlertDialog, {
                title: _t("Configuration"),
                body: _t("Your administrator paused the synchronization with the external calendar provider."),
            });
        }
    }

    goToFullEvent(resId, additionalContext) {
        this.actionService.doAction(
            {
                type: "ir.actions.act_window",
                res_model: "calendar.event",
                views: [[false, "form"]],
                res_id: resId || false,
            },
            {
                additionalContext,
            }
        );
    }

    getQuickCreateFormViewProps(record) {
        const props = super.getQuickCreateFormViewProps(record);
        const onDialogClosed = () => {
            this.model.load();
        };
        return {
            ...props,
            size: "md",
            goToFullEvent: (contextData) => {
                const fullContext = {
                    ...props.context,
                    ...contextData,
                };
                this.goToFullEvent(false, fullContext);
            },
            onRecordSaved: () => onDialogClosed(),
        };
    }

    async editRecord(record, context = {}) {
        if (record.id) {
            return this.goToFullEvent(record.id, context);
        }
    }

    /**
     * @override
     *
     * If the event is deleted by the organizer, the event is deleted, otherwise it is declined.
     */
    deleteRecord(record) {
        if (
            user.partnerId === record.attendeeId &&
            user.partnerId === record.rawRecord.partner_id[0]
        ) {
            if (record.rawRecord.recurrency) {
                this.openRecurringDeletionWizard(record);
            } else {
                super.deleteRecord(...arguments);
            }
        } else {
            // Decline event
            this.orm
                .call("calendar.attendee", "do_decline", [record.calendarAttendeeId])
                .then(this.model.load.bind(this.model));
        }
    }

    openRecurringDeletionWizard(record) {
        this.actionService.doAction(
            {
                type: "ir.actions.act_window",
                res_model: "calendar.popover.delete.wizard",
                views: [[false, "form"]],
                view_mode: "form",
                name: "Delete Recurring Event",
                context: { default_record: record.id },
                target: "new",
            },
            {
                onClose: () => {
                    location.reload();
                },
            }
        );
    }

    configureCalendarProviderSync(providerName) {
        this.actionService.doAction({
            name: _t("Connect your Calendar"),
            type: "ir.actions.act_window",
            res_model: "calendar.provider.config",
            views: [[false, "form"]],
            view_mode: "form",
            target: "new",
            context: {
                default_external_calendar_provider: providerName,
                dialog_size: "medium",
            },
        });
    }

    async onRedirectToMyPreferencesPage() {
        /**
         * Redirect user to My Preferences Page.
         * Currently there is no way to focus at the calendar page by means of the 'doAction' method.
         */
        const actionDescription = await this.orm.call("res.users", "action_get");
        actionDescription.res_id = user.userId;
        this.action.doAction(actionDescription);
    }
}

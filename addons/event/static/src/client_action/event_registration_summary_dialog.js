/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { Component, onMounted, useState } from "@odoo/owl";
import { isBarcodeScannerSupported } from "@web/webclient/barcode/barcode_scanner";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";

export class EventRegistrationSummaryDialog extends Component {
    static template = "event.EventRegistrationSummaryDialog";
    static components = { Dialog };
    static props = {
        close: Function,
        playSound: Function,
        doNextScan: Function,
        registration: Object,
    };

    setup() {
        this.actionService = useService("action");
        this.notification = useService("notification");
        this.orm = useService("orm");
        this.isBarcodeScannerSupported = isBarcodeScannerSupported();

        this.registration_status = useState({ value: this.registration.status});

        onMounted(() => {
            switch (this.props.registration.status) {
                case 'already_registered':
                case 'need_manual_confirmation':
                    this.props.playSound({ detail: "notify" });
                    break;
                case 'not_ongoing_event':
                case 'canceled_registration':
                    this.props.playSound({ detail: "error" });
                    break;
                default:
                    break;
            }
        });
    }

    get registration() {
        return this.props.registration;
    }

    async onRegistrationConfirm() {
        await this.orm.call("event.registration", "action_set_done", [this.registration.id]);
        this.registration_status.value = "confirmed_registration";
        this.notification.add(_t("Registration confirmed"));
    }

    onRegistrationPrintPdf() {
        this.actionService.doAction({
            type: "ir.actions.report",
            report_type: "qweb-pdf",
            report_name: `event.event_registration_report_template_badge/${this.registration.id}`,
        });
    }

    async onRegistrationView() {
        await this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: "event.registration",
            res_id: this.registration.id,
            views: [[false, "form"]],
            target: "current",
        });
        this.props.close();
    }

    async onScanNext() {
        this.props.close();
        this.props.doNextScan();
    }
}

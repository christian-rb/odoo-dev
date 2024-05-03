/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import { checkEmailValidity } from  "@mail/utils/common/format";
import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.websiteEventSendEmail = publicWidget.Widget.extend({
    selector: '.o_wevent_js_send_email',
    events: {
        'click': '_onSendEmailClick',
    },

    init() {
        this.notification = this.bindService("notification");
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {Event} ev
     */
    _onSendEmailClick: async function (ev) {
        const eventId = parseInt(ev.currentTarget.dataset.eventId, 10);
        const attendeesIds = JSON.parse(ev.currentTarget.dataset.attendeesIds);
        const ticketsHash = ev.currentTarget.dataset.ticketsHash;
        const emails = document.querySelector('#o_send_by_email_input').value;
        const emailInfo = checkEmailValidity(', ', emails)

        if (emails === "" || emailInfo.invalidEmails.length) {
            this._showError();
            console.log('Invalid Email');
        } else {
            this._hideError();
            const done = await rpc(`/event/${ eventId }/my_tickets_by_email`, {
                'registration_ids': attendeesIds,
                'tickets_hash': ticketsHash,
                'emails': emails
            });

            if (done) {
                this._showInfoMsg();
            }
        }
    },

    _showError: function () {
        const inputElement = document.querySelector('#o_send_by_email_input');
        inputElement.classList.add('is-invalid');
        this.notification.add(_t("Please enter valid email(s)"), { type: "danger" });
    },

    _hideError: function () {
        const inputElement = document.querySelector('#o_send_by_email_input');
        inputElement.classList.remove('is-invalid');
        this.notification.add(_t("Please enter valid email(s)"), { type: "danger" });
    },

    _showInfoMsg: function () {
        const inputMsgDiv = document.querySelector('.o_send_by_email_widget');
        inputMsgDiv.classList.add('d-none');
        const infoMsgDiv = document.querySelector('.o_send_by_email_info');
        infoMsgDiv.classList.remove('d-none');
    }
});

export default {
    websiteEventSendEmail: publicWidget.registry.websiteEventSendEmail,
};

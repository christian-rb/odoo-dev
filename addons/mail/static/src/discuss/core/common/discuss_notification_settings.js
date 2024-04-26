import { Component, useState } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { useService } from "@web/core/utils/hooks";

export class DiscussNotificationSettings extends Component {
    static props = ["*"];
    static template = "mail.DiscussNotificationSettings";

    setup() {
        this.store = useState(useService("mail.store"));
    }

    get selectedMuteDuration() {
        return browser.localStorage.getItem(`${this.store.self.localId}_selected_mute_duration`);
    }

    onChangeDisplayMuteDetails() {
        // If the user opens the mute menu, we set the default mute duration to forever
        this.store.settings.selected_mute_duration = this.store.settings.mute_until_dt
            ? false
            : this.store.settings.MUTES.find((m) => m.id === "forever").value;
    }

    onChangeMuteDuration(ev) {
        this.store.settings.selected_mute_duration = parseInt(ev.target.value);
    }

    onChangeCustomNotifications(value) {
        this.store.settings.setCustomNotifications(value);
    }
}

import { Record } from "@mail/core/common/record";
import { OTHER_LONG_TYPING } from "@mail/discuss/typing/common/typing_service";
import { browser } from "@web/core/browser/browser";
import { deserializeDateTime } from "@web/core/l10n/dates";

export class ChannelMember extends Record {
    static id = "id";
    /** @type {Object.<number, import("models").ChannelMember>} */
    static records = {};
    /** @returns {import("models").ChannelMember} */
    static get(data) {
        return super.get(data);
    }
    /** @returns {import("models").ChannelMember|import("models").ChannelMember[]} */
    static insert(data) {
        return super.insert(...arguments);
    }

    syncNewMessageSeparator = true;
    /** @type {string} */
    create_date;
    /** @type {number} */
    id;
    isThreadDisplayed = Record.attr(false, {
        compute() {
            if (this.store.discuss.isActive && !this.store.env.services.ui.isSmall) {
                return this.thread?.eq(this.store.discuss.thread);
            }
            return Boolean(this.store.ChatWindow.get({ thread: this.thread }));
        },
        onUpdate() {
            if (this.isThreadDisplayed && this.syncNewMessageSeparator) {
                this.newMessageSeparator = this.seen_message_id;
            }
            this.syncNewMessageSeparator = true;
        },
    });
    /** @type {luxon.DateTime} */
    last_interest_dt = Record.attr(undefined, { type: "datetime" });
    newMessageSeparator = Record.one("Message", {
        onUpdate() {
            this.syncNewMessageSeparator = false;
        },
    });
    persona = Record.one("Persona", { inverse: "channelMembers" });
    rtcSession = Record.one("RtcSession");
    storeAsOnInit = Record.one("Store", {
        eager: true,
        compute() {
            return this.store;
        },
        onAdd() {
            this.newMessageSeparator = this.seen_message_id;
        },
    });
    thread = Record.one("Thread", { inverse: "channelMembers" });
    threadAsSelf = Record.one("Thread", {
        compute() {
            if (this.store.self?.eq(this.persona)) {
                return this.thread;
            }
        },
    });
    fetched_message_id = Record.one("Message");
    seen_message_id = Record.one("Message");
    threadAsTyping = Record.one("Thread", {
        onAdd() {
            browser.clearTimeout(this.typingTimeoutId);
            this.typingTimeoutId = browser.setTimeout(
                () => (this.threadAsTyping = undefined),
                OTHER_LONG_TYPING
            );
        },
        onDelete() {
            browser.clearTimeout(this.typingTimeoutId);
        },
    });
    /** @type {number} */
    typingTimeoutId;

    get name() {
        return this.persona.nameOrDisplayName;
    }

    /**
     * @returns {string}
     */
    getLangName() {
        return this.persona.lang_name;
    }

    get memberSince() {
        return this.create_date ? deserializeDateTime(this.create_date) : undefined;
    }
}

ChannelMember.register();

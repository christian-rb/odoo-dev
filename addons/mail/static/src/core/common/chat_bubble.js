import { ImStatus } from "@mail/core/common/im_status";

import { Component, onWillStart, useState } from "@odoo/owl";

import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { useHover } from "@mail/utils/common/hooks";
import { useDropdownState } from "@web/core/dropdown/dropdown_hooks";
import { Dropdown } from "@web/core/dropdown/dropdown";

/**
 * @typedef {Object} Props
 * @extends {Component<Props, Env>}
 */
export class ChatBubble extends Component {
    static components = { ImStatus, Dropdown };
    static props = ["chatWindow"];
    static template = "mail.ChatBubble";

    setup() {
        this.store = useState(useService("mail.store"));
        this.hover = useHover(["root", "preview*"], () => {
            this.preview.isOpen = this.hover.isHover;
        });
        this.preview = useDropdownState();
        onWillStart(async () => {
            await this.store.channels.fetch();
        });
    }

    /** @returns {import("models").Thread} */
    get thread() {
        return this.props.chatWindow.thread;
    }

    get previewContent() {
        const lastMessage = this.thread.newestPersistentNotEmptyOfAllMessage;
        if (!lastMessage) {
            return false;
        }
        const selfAuthored = this.store.self.eq(lastMessage.author);
        return _t("%(authorName)s: %(body)s", {
            authorName: selfAuthored ? "You" : lastMessage.author.name,
            body: lastMessage.inlineBody,
        });
    }
}

import { ChatWindow } from "@mail/core/common/chat_window";
import { useHover } from "@mail/utils/common/hooks";
import { Component, useExternalListener, useState } from "@odoo/owl";

import { browser } from "@web/core/browser/browser";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { useDropdownState } from "@web/core/dropdown/dropdown_hooks";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { ChatBubble } from "./chat_bubble";

export class ChatHub extends Component {
    static components = { ChatBubble, ChatWindow, Dropdown };
    static props = [];
    static template = "mail.ChatHub";

    get chatHub() {
        return this.store.chatHub;
    }

    setup() {
        super.setup();
        this.store = useState(useService("mail.store"));
        this.ui = useState(useService("ui"));
        this.foldHover = useHover("fold");
        this.moreHover = useHover(["more-button", "more-menu*"], () => {
            this.more.isOpen = this.moreHover.isHover;
        });
        this.options = useDropdownState();
        this.more = useDropdownState();

        this.onResize();
        useExternalListener(browser, "resize", this.onResize);
    }

    onResize() {
        while (this.chatHub.visible.length > this.store.maxVisibleChatWindows) {
            this.chatHub.visible.at(-1).hide();
        }
        while (
            this.chatHub.visible.length < this.store.maxVisibleChatWindows &&
            this.store.hiddenChatWindows.length > 0
        ) {
            this.store.hiddenChatWindows[0].show();
        }
    }

    get unread() {
        let unreadCounter = 0;
        for (const chatWindow of this.store.hiddenChatWindows) {
            unreadCounter += chatWindow.thread.message_unread_counter;
        }
        return unreadCounter;
    }

    get visiblyFolded() {
        const chatBubbleLimit = this.store.chatBubbleLimit;
        return this.store.discuss.chatBubbles.slice(-chatBubbleLimit).reverse();
    }

    get hiddenlyFolded() {
        const chatBubbleLimit = this.store.chatBubbleLimit;
        const count = this.store.discuss.chatBubbles.length - chatBubbleLimit;
        if (count <= 0) {
            return [];
        }
        return this.store.discuss.chatBubbles.slice(0, count);
    }

    closeBubbles() {
        for (const bubble of this.store.discuss.chatBubbles) {
            bubble.close();
        }
    }

    hideBubbles() {
        this.store.chatHub.compact = true;
    }

    showBubbles() {
        this.store.chatHub.compact = false;
        this.more.isOpen = this.hiddenlyFolded.length !== 0;
    }
}

registry.category("main_components").add("mail.ChatHub", { Component: ChatHub });

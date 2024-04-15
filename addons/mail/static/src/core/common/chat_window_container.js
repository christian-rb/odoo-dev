import { ChatWindow } from "@mail/core/common/chat_window";
import { useHover } from "@mail/utils/common/hooks";
import { Component, useExternalListener, useState, onMounted, useRef, useEffect } from "@odoo/owl";

import { browser } from "@web/core/browser/browser";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { useDropdownState } from "@web/core/dropdown/dropdown_hooks";
import { localization } from "@web/core/l10n/localization";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { ChatBubble } from "./chat_bubble";

export class ChatWindowContainer extends Component {
    static components = { ChatBubble, ChatWindow, Dropdown };
    static props = [];
    static template = "mail.ChatWindowContainer";

    setup() {
        super.setup();
        this.store = useState(useService("mail.store"));
        this.ui = useState(useService("ui"));
        this.hiddenMenuRef = useRef("hiddenMenu");
        useEffect(
            () => this.setHiddenMenuOffset(),
            () => [this.store.hiddenChatWindows]
        );
        onMounted(() => this.setHiddenMenuOffset());
        this.bubbleContainerHover = useHover("bubble-container");
        this.moreHover = useHover(["more-button", "more-menu*"], () => {
            this.more.isOpen = this.moreHover.isHover;
        });
        this.store.usingChatBubbles = true;
        this.options = useDropdownState();
        this.more = useDropdownState();

        this.onResize();
        useExternalListener(browser, "resize", this.onResize);
    }

    setHiddenMenuOffset() {
        if (!this.hiddenMenuRef.el) {
            return;
        }
        const textDirection = localization.direction;
        const offsetFrom = textDirection === "rtl" ? "left" : "right";
        const visibleOffset =
            this.store.CHAT_WINDOW_END_GAP_WIDTH +
            this.store.maxVisibleChatWindows *
                (this.store.CHAT_WINDOW_WIDTH + this.store.CHAT_WINDOW_END_GAP_WIDTH);
        const oppositeFrom = offsetFrom === "right" ? "left" : "right";
        this.hiddenMenuRef.el.style = `${offsetFrom}: ${visibleOffset}px; ${oppositeFrom}: auto`;
    }

    onResize() {
        while (this.store.visibleChatWindows.length > this.store.maxVisibleChatWindows) {
            this.store.visibleChatWindows.at(-1).hide();
        }
        while (
            this.store.visibleChatWindows.length < this.store.maxVisibleChatWindows &&
            this.store.hiddenChatWindows.length > 0
        ) {
            this.store.hiddenChatWindows[0].show();
        }
        this.setHiddenMenuOffset();
    }

    get unread() {
        let unreadCounter = 0;
        for (const chatWindow of this.store.hiddenChatWindows) {
            unreadCounter += chatWindow.thread.message_unread_counter;
        }
        return unreadCounter;
    }

    get visible() {
        const chatBubbleLimit = this.store.chatBubbleLimit;
        return this.store.discuss.chatBubbles.slice(-chatBubbleLimit).reverse();
    }

    get hidden() {
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
        this.store.chatBubbleCompact = true;
    }

    showBubbles() {
        this.store.chatBubbleCompact = false;
        this.more.isOpen = this.hidden.length !== 0;
    }
}

registry
    .category("main_components")
    .add("mail.ChatWindowContainer", { Component: ChatWindowContainer });

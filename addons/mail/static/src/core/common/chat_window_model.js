import { Record } from "@mail/core/common/record";
import { assignDefined, rpcWithEnv } from "@mail/utils/common/misc";

import { _t } from "@web/core/l10n/translation";

/** @typedef {{ thread?: import("models").Thread, folded?: boolean, replaceNewMessageChatWindow?: boolean }} ChatWindowData */

let rpc;

export class ChatWindow extends Record {
    static id = "thread";
    /** @type {Object<number, import("models").ChatWindow} */
    static records = {};
    /** @returns {import("models").ChatWindow} */
    static get(data) {
        return super.get(data);
    }
    /** @returns {import("models").ChatWindow|import("models").ChatWindow[]} */
    static insert() {
        return super.insert(...arguments);
    }
    static new() {
        rpc = rpcWithEnv(this.store.env);
        return super.new(...arguments);
    }
    /**
     * @param {ChatWindowData} [data]
     * @returns {import("models").ChatWindow}
     */
    static _insert(data = {}) {
        const chatWindow = this.store.chatHub.windows.find((w) => w.thread?.eq(data.thread));
        if (!chatWindow) {
            /** @type {import("models").ChatWindow} */
            const chatWindow = this.preinsert(data);
            assignDefined(chatWindow, data);
            let index;
            const visible = this.store.chatHub.visible;
            const maxVisible = this.store.maxVisibleChatWindows;
            if (!data.replaceNewMessageChatWindow) {
                if (maxVisible <= this.store.chatHub.windows.length) {
                    const swaped = visible[visible.length - 1];
                    index = visible.length - 1;
                    swaped.toggleFold();
                } else {
                    index = this.store.chatHub.windows.length;
                }
            } else {
                const newMessageChatWindowIndex = this.store.chatHub.windows.findIndex(
                    (w) => !w.thread
                );
                index =
                    newMessageChatWindowIndex !== -1
                        ? newMessageChatWindowIndex
                        : this.store.chatHub.windows.length;
            }
            this.store.chatHub.windows.splice(
                index,
                data.replaceNewMessageChatWindow ? 1 : 0,
                chatWindow
            );
            return chatWindow; // return reactive version
        }
        if (chatWindow.hidden) {
            chatWindow.makeVisible();
        }
        assignDefined(chatWindow, data);
        return chatWindow;
    }

    thread = Record.one("Thread");
    autofocus = 0;
    folded = false;
    hidden = false;
    openMessagingMenuOnClose = false;

    get displayName() {
        return this.thread?.displayName ?? _t("New message");
    }

    get isOpen() {
        return !this.folded && !this.hidden;
    }

    async close(options = {}) {
        const { escape = false } = options;
        if (!this.hidden && this.store.maxVisibleChatWindows < this.store.chatHub.windows.length) {
            const swaped = this.store.hiddenChatWindows[0];
            swaped.hidden = false;
            swaped.folded = false;
        }
        const index = this.store.chatHub.windows.findIndex((w) => w.eq(this));
        if (index > -1) {
            this.store.chatHub.windows.splice(index, 1);
        }
        const thread = this.thread;
        if (thread) {
            thread.state = "closed";
        }
        if (escape && this.store.chatHub.windows.length > 0) {
            this.store.chatHub.windows.at(index - 1).focus();
        }
        await this._onClose(options);
        this.delete();
    }

    focus() {
        this.autofocus++;
    }

    hide() {
        this.hidden = true;
    }

    makeVisible() {
        const swaped = this.store.chatHub.visible.at(-1);
        swaped.hide();
        this.show({ notifyState: false });
    }

    notifyState() {
        if (this.store.env.services.ui.isSmall || this.thread?.isTransient) {
            return;
        }
        if (this.thread?.model === "discuss.channel") {
            this.thread.foldStateCount++;
            return rpc(
                "/discuss/channel/fold",
                {
                    channel_id: this.thread.id,
                    state: this.thread.state,
                    state_count: this.thread.foldStateCount,
                },
                { shadow: true }
            );
        }
    }

    show({ notifyState = true } = {}) {
        this.hidden = false;
        this.folded = false;
        this.thread.state = "open";
        if (notifyState) {
            this.notifyState();
        }
    }

    toggleFold() {
        if (!this.thread) {
            return this.store.closeNewMessage();
        }
        this.folded = !this.folded;
        this.thread.state = this.folded ? "folded" : "open";
        this.notifyState();
    }

    async _onClose({ notifyState = true } = {}) {
        if (notifyState) {
            this.notifyState();
        }
    }
}

ChatWindow.register();

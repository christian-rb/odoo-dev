import { Record } from "@mail/core/common/record";
import { rpcWithEnv } from "@mail/utils/common/misc";

/** @typedef {{ thread?: import("models").Thread }} ChatBubbleData */

let rpc;
export class ChatBubble extends Record {
    static id = "thread";
    /** @type {Object<number, import("models").ChatBubble} */
    static records = {};
    /** @returns {import("models").ChatBubble} */
    static get(data) {
        return super.get(data);
    }
    /** @returns {import("models").ChatBubble|import("models").ChatBubble[]} */
    static insert() {
        return super.insert(...arguments);
    }
    static new() {
        rpc = rpcWithEnv(this.store.env);
        return super.new(...arguments);
    }
    /**
     * @param {ChatBubbleData} [data]
     * @returns {import("models").ChatBubble}
     */
    static _insert(data = {}) {
        const chatBubble = super._insert(...arguments);
        if (!this.store.discuss.chatBubbles.includes(chatBubble)) {
            this.store.discuss.chatBubbles.add(chatBubble);
        }
        return chatBubble;
    }

    thread = Record.one("Thread");

    async close(options = {}) {
        this.thread.state = "closed";
        await this._onClose(options);
        this.delete();
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

    async _onClose({ notifyState = true } = {}) {
        if (notifyState) {
            this.notifyState();
        }
    }
}

ChatBubble.register();

import { Record } from "./record";

export class ChatHub extends Record {
    /** @returns {import("models").ChatHub} */
    static get(data) {
        return super.get(data);
    }
    /** @returns {import("models").ChatHub|import("models").ChatHub[]} */
    static insert(data) {
        return super.insert(...arguments);
    }

    windows = Record.many("ChatWindow");
    compact = false;

    get visible() {
        return this.windows.filter((w) => !w.hidden);
    }
}

ChatHub.register();

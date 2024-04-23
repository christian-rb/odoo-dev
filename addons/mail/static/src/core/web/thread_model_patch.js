import { Thread } from "@mail/core/common/thread_model";

import { patch } from "@web/core/utils/patch";
import { Record } from "../common/record";

patch(Thread.prototype, {
    /** @type {integer|undefined} */
    recipientsCount: undefined,
    setup() {
        super.setup();
        this.recipients = Record.many("Follower");
        this.activities = Record.many("Activity", {
            sort: (a, b) => {
                if (a.date_deadline === b.date_deadline) {
                    return a.id - b.id;
                }
                return a.date_deadline < b.date_deadline ? -1 : 1;
            },
            onDelete(r) {
                r.remove();
            },
        });
    },
    get recipientsFullyLoaded() {
        return this.recipientsCount === this.recipients.length;
    },
    closeChatWindow() {
        const chatWindow = this.store.chatHub.windows.find((w) => w.thread?.eq(this));
        chatWindow?.close({ notifyState: false });
    },
    async leave() {
        this.closeChatWindow();
        super.leave(...arguments);
    },
    async loadMoreFollowers() {
        const followers = await this.store.env.services.orm.call(
            this.model,
            "message_get_followers",
            [[this.id], this.followers.at(-1).id]
        );
        Record.MAKE_UPDATE(() => {
            for (const data of followers) {
                const follower = this.store.Follower.insert({
                    thread: this,
                    ...data,
                });
                if (follower.notEq(this.selfFollower)) {
                    this.followers.add(follower);
                }
            }
        });
    },
    async loadMoreRecipients() {
        const recipients = await this.store.env.services.orm.call(
            this.model,
            "message_get_followers",
            [[this.id], this.recipients.at(-1).id],
            { filter_recipients: true }
        );
        Record.MAKE_UPDATE(() => {
            for (const data of recipients) {
                this.recipients.add({ thread: this, ...data });
            }
        });
    },
    open(replaceNewMessageChatWindow, options) {
        if (!this.store.discuss.isActive && !this.store.env.services.ui.isSmall) {
            this.openChatWindow(replaceNewMessageChatWindow, options);
            return;
        }
        if (this.store.env.services.ui.isSmall && this.model === "discuss.channel") {
            this.openChatWindow(replaceNewMessageChatWindow, options);
            return;
        }
        if (this.model !== "discuss.channel") {
            this.store.env.services.action.doAction({
                type: "ir.actions.act_window",
                res_id: this.id,
                res_model: this.model,
                views: [[false, "form"]],
            });
            return;
        }
        super.open(replaceNewMessageChatWindow);
    },
    async unpin() {
        const chatWindow = this.store.chatHub.windows.find((w) => w.thread?.eq(this));
        await chatWindow?.close();
        super.unpin(...arguments);
    },
});

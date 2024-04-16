import { SESSION_STATE } from "@im_livechat/embed/common/livechat_service";
import { FeedbackPanel } from "@im_livechat/embed/common/feedback_panel/feedback_panel";

import { ChatWindow } from "@mail/core/common/chat_window";

import { useState, toRaw } from "@odoo/owl";

import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { CloseConfirmation } from "./closeConfirmation";

Object.assign(ChatWindow.components, { FeedbackPanel, CloseConfirmation });

patch(ChatWindow.prototype, {
    setup() {
        super.setup(...arguments);
        this.livechatService = useService("im_livechat.livechat");
        this.chatbotService = useState(useService("im_livechat.chatbot"));
        this.livechatState = useState({
            hasFeedbackPanel: false,
            showCloseConfirmation: false,
            closeFeedback: false,
        });
    },

    async close() {
        if (this.thread?.channel_type !== "livechat") {
            return super.close();
        }
        const chatWindow = toRaw(this.props.chatWindow);
        if (chatWindow.folded) {
            chatWindow.makeVisible();
        }
        this.livechatState.showCloseConfirmation = true;
        if(this.livechatState.closeFeedback) {
            await this.closeChatWindow();
        }
    },

    async closeChatWindow() {
        this.thread?.delete();
        await super.close();
    },

    async onLeaveConversation() {
        if (this.livechatService.state === SESSION_STATE.PERSISTED) {
            this.livechatState.hasFeedbackPanel = true;
            this.props.chatWindow.show({ notifyState: false });
            this.livechatState.closeFeedback = true;
        } else {
            await this.closeChatWindow();
        }
        this.livechatService.leave();
        this.chatbotService.stop();
    },

    closeConfirmation() {
        this.livechatState.showCloseConfirmation = false;
    },
});

import { SuggestionService } from "@mail/core/common/suggestion_service";
import { cleanTerm } from "@mail/utils/common/format";

import { patch } from "@web/core/utils/patch";

patch(SuggestionService.prototype, {
    /** @override */
    getSupportedDelimiters(thread) {
        const res = super.getSupportedDelimiters(...arguments);
        return thread.channel_type === "livechat"
            ? [...res, [" ", 4]].filter((delimiter) => delimiter.at(0) !== "#")
            : res;
    },
    /** @override */
    async fetchSuggestions({ delimiter, term }, { thread } = {}) {
        if (delimiter === " ") {
            return await this.store.chatbotData.fetch();
        }
        await super.fetchSuggestions(...arguments);
    },
    /** @override */
    searchSuggestions({ delimiter, term }, { thread, composer, sort = false } = {}) {
        if (delimiter === " " && composer?.subCommandParent === "bot") {
            return this.searchChatbotSuggestions(cleanTerm(term));
        }
        return super.searchSuggestions(...arguments);
    },
    searchChatbotSuggestions(cleanedSearchTerm) {
        return {
            type: "Chatbot",
            suggestions: Object.values(this.store.ChatbotScript.records).filter((chatbot) => {
                return cleanTerm(chatbot.name).includes(cleanedSearchTerm);
            }),
        };
    },
});

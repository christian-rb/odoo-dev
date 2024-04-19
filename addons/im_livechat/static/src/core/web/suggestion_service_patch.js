import { SuggestionService } from "@mail/core/common/suggestion_service";
import { cleanTerm } from "@mail/utils/common/format";

import { patch } from "@web/core/utils/patch";

patch(SuggestionService.prototype, {
    /** @override */
    getSupportedDelimiters(thread, composer) {
        const res = super.getSupportedDelimiters(...arguments);
        if (thread.channel_type === "livechat") {
            if (composer.command?.hasSubCommand) {
                res.push([" ", composer.command.endPosition]);
            }
            return res.filter((delimiter) => delimiter.at(0) !== "#");
        }
        return res;
    },
    /** @override */
    async fetchSuggestions({ delimiter, term }, { composer, thread } = {}) {
        if (delimiter === " " && composer.command?.name === "bot") {
            return await this.store.chatbotData.fetch();
        }
        await super.fetchSuggestions(...arguments);
    },
    /** @override */
    searchSuggestions({ delimiter, term }, { thread, composer, sort = false } = {}) {
        if (delimiter === " " && composer.command?.name === "bot") {
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

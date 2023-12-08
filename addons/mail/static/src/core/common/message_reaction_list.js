import { Component, markup } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

export class MessageReactionList extends Component {
    static template = "mail.MessageReaction.List";
    static props = {
        id: { type: Number, required: true },
        close: { type: Function, required: true },
        reaction: { type: Object, required: true },
        openReactionMenu: { type: Function, required: true },
    };

    getReactionSummary() {
        const reaction = this.props.reaction;
        const [name1, name2, name3] = reaction.personas.map((persona) => persona.nameOrDisplayName);
        switch (reaction.count) {
            case 1:
                return _t("%(content)s reacted by %(name1)s", {
                    content: reaction.content,
                    name1,
                });

            case 2:
                return _t("%(content)s reacted by %(name1)s and %(name2)s", {
                    content: reaction.content,
                    name1,
                    name2,
                });

            case 3:
                return _t("%(content)s reacted by %(name1)s, %(name2)s and %(name3)s", {
                    content: reaction.content,
                    name1,
                    name2,
                    name3,
                });
            default:
                return markup(_t(
                    "%(content)s reacted by %(name1)s, %(name2)s, %(name3)s and <span class='btn-link'>%(count)s %(otherText)s</span>",
                    {
                        content: reaction.content,
                        name1,
                        name2,
                        name3,
                        count: reaction.personas.length - 3,
                        otherText: reaction.personas.length - 3 === 1 ? "other" : "others",
                    }
                ));
        }
    }

    manageReactionMenu(reaction) {
        this.props.openReactionMenu(reaction);
        this.props.close();
    }
}

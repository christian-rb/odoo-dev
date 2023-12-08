import { MessageReactionList } from "@mail/core/common/message_reaction_list";
import { usePopover } from "@web/core/popover/popover_hook";

import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class MessageReactions extends Component {
    static props = ["message", "openReactionMenu"];
    static template = "mail.MessageReactions";
    static components = { MessageReactionList };

    setup() {
        super.setup();
        this.store = useState(useService("mail.store"));
        this.ui = useService("ui");
        this.reactionOpened = false;
        this.reactionPopover = usePopover(MessageReactionList, {
            closeOnHoverAway: true,
            popoverClass: "o-mail-MessageReactionList-Popover",
            position: "bottom-start",
        });
        this.lastedOpenedId = 0;
    }

    hasSelfReacted(reaction) {
        return this.store.self.in(reaction.personas);
    }

    onClickReaction(reaction) {
        if (this.hasSelfReacted(reaction)) {
            reaction.remove();
        } else {
            this.props.message.react(reaction.content);
        }
    }

    onContextMenu(ev) {
        if (this.ui.isSmall) {
            ev.preventDefault();
            this.props.openReactionMenu();
        }
    }
    openReactions(params) {
        const target = params.ev.currentTarget;
        const reaction = params.reaction;
        if (
            !this.reactionPopover.isOpen ||
            (this.lastedOpenedId && reaction.messageId !== this.lastedOpenedId)
        ) {
            this.reactionPopover.open(target, {
                id: reaction.message.id,
                reaction: params.reaction,
                openReactionMenu: this.props.openReactionMenu,
            });
            this.lastedOpenedId = reaction.messageId;
        }
    }
}

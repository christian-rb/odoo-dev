import { Component, useRef, useEffect } from "@odoo/owl";

export class CloseConfirmation extends Component {
    static template = "im_livechat.closeConfirmation";
    static props = ["onClickClose?", "onLeaveConversation?"];

    setup() {
        this.confirmationDialog = useRef("leaveConversation");
        useEffect(
            () => {
                if (this.confirmationDialog.el) {
                    this.confirmationDialog.el.focus();
                }
            },
            () => [this.confirmationDialog.el]
        );
    }

    onKeydown(ev) {
        ev.stopPropagation();
        if (ev.key === "Escape") {
            this.props.onClickClose();
        } else if (ev.key === "Enter") {
            this.props.onLeaveConversation();
        }
    }

    onClick(ev) {
        const targetClass = ev.target.classList;
        switch (true) {
            case targetClass.contains("o-livechat-closeConfirmation-overlay"):
            case targetClass.contains("btn-close"):
                this.props.onClickClose();
                break;
            case targetClass.contains("o-livechat-closeConfirmation-leave"):
                this.props.onLeaveConversation();
                break;
            default:
                break;
        }
    }
}

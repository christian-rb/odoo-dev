/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";

import { registry } from "@web/core/registry";
import { ShareBar } from "@social_share/share_campaign/share_campaign_share_button";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

import { renderToMarkup } from "@web/core/utils/render";
import { useService } from "@web/core/utils/hooks";
import { Component, markup, useState, useEffect } from "@odoo/owl";

class Sharecampaign extends Component {
    static components = {
        ShareBar,
    };
    static template = "snshare.Sharecampaign";

    setup() {
        this.dialog = useService("dialog");
        this.state = useState({
            message: this.props.linkSharedMessage ? markup(this.props.linkSharedMessage) : "",
            rewardUrl: this.props.linkSharedRewardUrl,
        });
        this.busService = this.env.services.bus_service;
        if (this.props.uuid) {
            this.busService.addChannel(`snshare_url_target-${this.props.uuid}`);
            this.busService.subscribe("snshare/share_url_target", ({ message, rewardUrl }) => {
                this.state.message = markup(message);
                this.state.rewardUrl = rewardUrl;
            });
        }
        useEffect(
            () => {
                if (this.state.message || this.state.rewardUrl) {
                    this.dialog.add(ConfirmationDialog, {
                        title: _t("Thank You!"),
                        body: renderToMarkup("snshare.ThankMessage", {
                            message: this.state.message,
                            rewardUrl: this.state.rewardUrl,
                        }),
                        confirmLabel: _t("Close"),
                    });
                }
            },
            () => [this.state.message || this.state.rewardUrl],
        );
    }
}

registry.category("public_components").add("snshare_campaign", Sharecampaign);

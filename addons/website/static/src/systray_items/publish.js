/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { deserializeDateTime } from "@web/core/l10n/dates";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { CheckBox } from '@web/core/checkbox/checkbox';
import { RelativePublishTime } from "./relative_publish_time";
import { useService, useBus } from '@web/core/utils/hooks';
import { Component, useState, onWillStart } from "@odoo/owl";

const websiteSystrayRegistry = registry.category('website_systray');

class PublishSystray extends Component {
    static template = "website.WebsitePublishSystray";
    static components = {
        CheckBox,
        RelativePublishTime,
    };
    static props = {};

    setup() {
        this.website = useService('website');
        this.actionService = useService('action');
        this.websiteCustomMenus = useService('website_custom_menus');
        this.state = useState({
            published: false,
            scheduled: false,
            publishAt: false,
            formattedPublishAt: false,
            processing: false,
        })
        onWillStart(this._updateState)
        useBus(websiteSystrayRegistry, 'CONTENT-UPDATED', this._updateState);
    }

    _updateState() {
        this.state.published = this.website.currentWebsite.metadata.isPublished;
        this.state.scheduled = this.website.currentWebsite.metadata.scheduled;
        this.state.publishAt = this.website.currentWebsite.metadata.publishAt
            ? deserializeDateTime(
                this.website.currentWebsite.metadata.publishAt
            )
            : false;
        this.state.formattedPublishAt = this.state.publishAt ? this.state.publishAt.toLocaleString(luxon.DateTime.DATETIME_MED) : false;
    }

    triggerPublish() {
        this.state.published = true;
        this.state.scheduled = false;
        this.state.publishAt = false;
        this.state.formattedPublishAt = false;
    }

    editInBackend() {
        const { metadata: { mainObject } } = this.website.currentWebsite;
        if (mainObject.model === "website.page") {
            this.websiteCustomMenus.open({
                xmlid: "website.menu_page_properties"
            });
        }
        else {
            this.actionService.doAction({
                res_model: mainObject.model,
                res_id: mainObject.id,
                views: [[false, "form"]],
                type: "ir.actions.act_window",
                view_mode: "form",
            });
        }
    }

    get label() {
        return this.state.published ? _t("Published") : _t("Unpublished");
    }

    /**
     * @todo event handlers should probably never return a Promise using OWL,
     * to adapt in master.
     */
    async publishContent() {
        if (this.state.processing) {
            return;
        }
        this.state.processing = true;
        this.state.published = !this.state.published;
        const { metadata: { mainObject } } = this.website.currentWebsite;
        return rpc('/website/publish', {
            id: mainObject.id,
            object: mainObject.model,
        }).then(
            (published) => {
                this.state.published = published;
                if (this.state.published) {
                    // Set the scheduled state to false if the page is published
                    this.state.scheduled = false;
                    this.state.publishAt = false;
                }
                this.state.processing = false;
                return published;
            },
            err => {
                this.state.published = !this.state.published;
                this.state.processing = false;
                throw err;
            }
        );
    }
}

export const systrayItem = {
    Component: PublishSystray,
    isDisplayed: env => env.services.website.currentWebsite && env.services.website.currentWebsite.metadata.canPublish,
};

websiteSystrayRegistry.add("Publish", systrayItem, { sequence: 12 });

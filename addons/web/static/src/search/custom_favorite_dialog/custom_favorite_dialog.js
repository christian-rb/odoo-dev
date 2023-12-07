/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { CheckBox } from "@web/core/checkbox/checkbox";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";

import { Component, useRef, useState } from "@odoo/owl";

export class CustomFavoriteDialog extends Component {
    static template = "web.CustomFavoriteDialog";
    static components = { CheckBox, Dialog };
    static props = {
        title: String,
        onConfirm: Function,
        close: Function,
        description: { type: String, optional: true },
        showSharedCheckBox: { type: Boolean, optional: true },
        favoriteDescriptions: { type: Array, element: String, optional: true },
    };
    static defaultProps = {
        description: "",
        showSharedCheckBox: true,
        favoriteDescriptions: [],
    };

    setup() {
        this.notificationService = useService("notification");
        this.descriptionRef = useRef("description");
        this.state = useState({
            description: this.props.description,
            isDefault: false,
            isShared: false,
        });
    }

    /**
     * @param {Event} ev
     */
    saveFavorite(ev) {
        if (!this.state.description) {
            this.notificationService.add(_t("A name for your favorite filter is required."), {
                type: "danger",
            });
            ev.stopPropagation();
            return this.descriptionRef.el.focus();
        }
        const hasAlreadyFavoriteWithSameDescription = this.props.favoriteDescriptions.some(
            (d) => d === this.state.description
        );
        if (hasAlreadyFavoriteWithSameDescription) {
            this.notificationService.add(_t("A filter with same name already exists."), {
                type: "danger",
            });
            ev.stopPropagation();
            return this.descriptionRef.el.focus();
        }
        this.props.onConfirm({ ...this.state });
        this.props.close();
    }

    /**
     * @param {boolean} checked
     */
    onDefaultCheckboxChange(checked) {
        this.state.isDefault = checked;
        if (checked) {
            this.state.isShared = false;
        }
    }

    /**
     * @param {boolean} checked
     */
    onShareCheckboxChange(checked) {
        this.state.isShared = checked;
        if (checked) {
            this.state.isDefault = false;
        }
    }

    onInputKeydown(ev) {
        if (ev.key === "Enter") {
            this.saveFavorite(ev);
        }
    }
}

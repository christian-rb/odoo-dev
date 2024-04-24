import { _t } from "@web/core/l10n/translation";
import { browser } from "@web/core/browser/browser";
import { getActiveHotkey } from "@web/core/hotkeys/hotkey_service";
import { Pager } from "@web/core/pager/pager";
import { useService } from "@web/core/utils/hooks";
import { SearchBar } from "../search_bar/search_bar";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { useCommand } from "@web/core/commands/command_hook";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { useHotkey } from "@web/core/hotkeys/hotkey_hook";
import { useSortable } from "@web/core/utils/sortable_owl";
import { user } from "@web/core/user";
import { AccordionItem } from "@web/core/dropdown/accordion_item";
import { CheckBox } from "@web/core/checkbox/checkbox";
import { makeContext } from "@web/core/context";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

import {
    Component,
    useState,
    onMounted,
    useExternalListener,
    useRef,
    useEffect,
    onWillStart,
} from "@odoo/owl";

const STICKY_CLASS = "o_mobile_sticky";

/**
 * @typedef TopbarAction
 * @property {number} id
 * @property {[number, string] | false} parent_action_id
 * @property {string} name
 * @property {number} sequence
 * @property {number} parent_res_id
 * @property {string} parent_res_model
 * @property {[number, string] | false} action_id
 * @property {string} python_action
 * @property {[number, string] | false} user_id
 * @property {boolean} is_deletable
 * @property {string} default_view_mode
 * @property {string} filter_ids
 * @property {string} domain
 * @property {string} context
 */

export class ControlPanel extends Component {
    static template = "web.ControlPanel";
    static components = {
        Pager,
        SearchBar,
        Dropdown,
        DropdownItem,
        AccordionItem,
        CheckBox,
    };
    static props = {
        display: { type: Object, optional: true },
        slots: { type: Object, optional: true },
    };

    setup() {
        this.actionService = useService("action");
        this.pagerProps = this.env.config.pagerProps
            ? useState(this.env.config.pagerProps)
            : undefined;
        this.notificationService = useService("notification");
        this.breadcrumbs = useState(this.env.config.breadcrumbs);
        this.orm = useService("orm");
        this.dialogService = useService("dialog");

        this.root = useRef("root");
        this.newActionNameRef = useRef("newActionNameRef");
        this.isTopbarActionsOrderModifiable = false;

        /**
         * The visible topbar actions are unique to each user and to each res_id. The visible actions chosen by the
         * user are stored in the local storage in a key corresponding to a combination of the actionId, the activeId
         * and the currrent userId. Each key contains a dict. The keys of the latter are the id of the visible topbar
         * actions.
         */
        const parentActionId =
            this.env.config.parentActionId ||
            this.env.config.topbarActions?.[0]?.parent_action_id[0] ||
            "";
        this.topbarActionsVisibilityKey = `visibleTopbarActions${parentActionId}+${
            this.env.searchModel?.globalContext.active_id || ""
        }+${user.userId}`;

        this.topbarVisibilityKey = `visibleTopbar${parentActionId}+${
            this.env.searchModel?.globalContext.active_id || ""
        }+${user.userId}`;

        this.topbarOrderKey = `orderTopbar${parentActionId}+${
            this.env.searchModel?.globalContext.active_id || ""
        }+${user.userId}`;

        this.state = useState({
            showSearchBar: false,
            showMobileSearch: false,
            showViewSwitcher: false,
            topbarInfos: {
                showTopbar:
                    this.env.config.topbarActions?.length > 0 &&
                    (!!this.env.config.parentActionId ||
                        !!JSON.parse(browser.localStorage.getItem(this.topbarVisibilityKey))),
                topbarActions: this.env.config?.topbarActions || [],
                newActionIsShared: false,
                newActionName: `Custom ${this.currentTopbarAction?.name || "Topbar Action"}`,
                visibleTopbarActions:
                    JSON.parse(browser.localStorage.getItem(this.topbarActionsVisibilityKey)) || {},
                currentTopbarAction: this.currentTopbarAction,
            },
        });

        this.onScrollThrottledBound = this.onScrollThrottled.bind(this);

        const { viewSwitcherEntries, viewType } = this.env.config;
        for (const view of viewSwitcherEntries || []) {
            useCommand(_t("Show %s view", view.name), () => this.switchView(view.type), {
                category: "view_switcher",
                isAvailable: () => view.type !== viewType,
            });
        }

        if (viewSwitcherEntries?.length > 1) {
            useHotkey(
                "alt+shift+v",
                () => {
                    this.cycleThroughViews();
                },
                {
                    bypassEditableProtection: true,
                    withOverlay: () => this.root.el.querySelector("nav.o_cp_switch_buttons"),
                }
            );
        }

        onWillStart(async () => {
            // This is meant to be overriden
            this.isTopbarActionsOrderModifiable = await user.hasGroup("base.group_system");
            // If there is no visible topbar actions, the current action (if it exists) is put by default
            if (!Object.keys(this.state.topbarInfos.visibleTopbarActions).includes("0")) {
                this._setVisibility(0);
            }
            const topbarOrderLocalStorageKey = browser.localStorage.getItem(this.topbarOrderKey);
            if (topbarOrderLocalStorageKey) {
                this._sortTopbarActions(JSON.parse(topbarOrderLocalStorageKey));
            }
        });

        useExternalListener(window, "click", this.onWindowClick);
        useEffect(() => {
            if (
                !this.env.isSmall ||
                ("adaptToScroll" in this.display && !this.display.adaptToScroll)
            ) {
                return;
            }
            const scrollingEl = this.getScrollingElement();
            scrollingEl.addEventListener("scroll", this.onScrollThrottledBound);
            this.root.el.style.top = "0px";
            return () => {
                scrollingEl.removeEventListener("scroll", this.onScrollThrottledBound);
            };
        });
        onMounted(() => {
            if (
                !this.env.isSmall ||
                ("adaptToScroll" in this.display && !this.display.adaptToScroll)
            ) {
                return;
            }
            this.oldScrollTop = 0;
            this.lastScrollTop = 0;
            this.initialScrollTop = this.getScrollingElement().scrollTop;
        });

        this.mainButtons = useRef("mainButtons");

        useEffect(() => {
            // on small screen, clean-up the dropdown elements
            const dropdownButtons = this.mainButtons.el.querySelectorAll(
                ".o_control_panel_collapsed_create.dropdown-menu button"
            );
            if (!dropdownButtons.length) {
                this.mainButtons.el
                    .querySelectorAll(
                        ".o_control_panel_collapsed_create.dropdown-menu, .o_control_panel_collapsed_create.dropdown-toggle"
                    )
                    .forEach((el) => el.classList.add("d-none"));
                this.mainButtons.el
                    .querySelectorAll(".o_control_panel_collapsed_create.btn-group")
                    .forEach((el) => el.classList.remove("btn-group"));
                return;
            }
            for (const button of dropdownButtons) {
                for (const cl of Array.from(button.classList)) {
                    button.classList.toggle(cl, !cl.startsWith("btn-"));
                }
                button.classList.add("dropdown-item", "btn", "btn-link");
            }
        });

        useSortable({
            enable: () => this.isTopbarActionsOrderModifiable,
            ref: this.root,
            elements: ".o_draggable",
            cursor: "move",
            delay: 200,
            tolerance: 10,
            onWillStartDrag: (params) => this._sortTopbarActionStart(params),
            onDrop: (params) => this._sortTopbarActionDrop(params),
        });
    }

    getDropdownClass(action) {
        return (!this.env.isSmall && this._checkValueLocalStorage(action)) ||
            (this.env.isSmall && this.state.topbarInfos.currentTopbarAction?.id === action.id)
            ? "selected"
            : "";
    }

    getScrollingElement() {
        return this.root.el.parentElement;
    }

    /**
     * @returns {TopbarAction}
     */
    get currentTopbarAction() {
        if (!this.env.config) {
            return {};
        }
        const { topbarActions, currentTopbarActionId } = this.env.config;
        return topbarActions?.find(({ id }) => id === currentTopbarActionId) || topbarActions?.[0];
    }

    /**
     * Reset mobile search state
     */
    resetSearchState() {
        Object.assign(this.state, {
            showSearchBar: false,
            showMobileSearch: false,
            showViewSwitcher: false,
        });
    }

    /**
     * @returns {Object}
     */
    get display() {
        return {
            layoutActions: true,
            ...this.props.display,
        };
    }

    /**
     * Called when an element of the breadcrumbs is clicked.
     *
     * @param {string} jsId
     */
    onBreadcrumbClicked(jsId) {
        this.actionService.restore(jsId);
    }

    onClickShowTopbar() {
        if (this.state.topbarInfos.showTopbar) {
            browser.localStorage.removeItem(this.topbarVisibilityKey);
        } else {
            browser.localStorage.setItem(this.topbarVisibilityKey, true);
        }
        this.state.topbarInfos.showTopbar = !this.state.topbarInfos.showTopbar;
    }

    /**
     * Show or hide the control panel on the top screen.
     * The function is throttled to avoid refreshing the scroll position more
     * often than necessary.
     */
    onScrollThrottled() {
        if (this.isScrolling) {
            return;
        }
        this.isScrolling = true;
        browser.requestAnimationFrame(() => (this.isScrolling = false));

        const scrollTop = this.getScrollingElement().scrollTop;
        const delta = Math.round(scrollTop - this.oldScrollTop);

        if (scrollTop > this.initialScrollTop) {
            // Beneath initial position => sticky display
            this.root.el.classList.add(STICKY_CLASS);
            if (delta < 0) {
                // Going up
                this.lastScrollTop = Math.min(0, this.lastScrollTop - delta);
            } else {
                // Going down | not moving
                this.lastScrollTop = Math.max(
                    -this.root.el.offsetHeight,
                    -this.root.el.offsetTop - delta
                );
            }
            this.root.el.style.top = `${this.lastScrollTop}px`;
        } else {
            // Above initial position => standard display
            this.root.el.classList.remove(STICKY_CLASS);
            this.lastScrollTop = 0;
        }

        this.oldScrollTop = scrollTop;
    }

    /**
     * Allow to switch from the current view to another.
     * Called when a view is clicked in the view switcher
     * and reset mobile search state on switch view.
     *
     * @param {ViewType} viewType
     */
    switchView(viewType) {
        this.resetSearchState();
        this.actionService.switchView(viewType);
    }

    cycleThroughViews() {
        const currentViewType = this.env.config.viewType;
        const viewSwitcherEntries = this.env.config.viewSwitcherEntries;
        const currentIndex = viewSwitcherEntries.findIndex(
            (entry) => entry.type === currentViewType
        );
        const nextIndex = (currentIndex + 1) % viewSwitcherEntries.length;
        this.switchView(viewSwitcherEntries[nextIndex].type);
    }

    /**
     * @private
     * @param {MouseEvent} ev
     */
    onWindowClick(ev) {
        if (this.state.showViewSwitcher && !ev.target.closest(".o_cp_switch_buttons")) {
            this.state.showViewSwitcher = false;
        }
    }

    /**
     * @param {KeyboardEvent} ev
     */
    onMainButtonsKeydown(ev) {
        const hotkey = getActiveHotkey(ev);
        if (hotkey === "arrowdown") {
            this.env.searchModel.trigger("focus-view");
            ev.preventDefault();
            ev.stopPropagation();
        }
    }

    /**
     * @param {TopbarAction} action
     */
    _checkValueLocalStorage(action) {
        const actionIdStr = action.id.toString();
        return this.state.topbarInfos.visibleTopbarActions[actionIdStr];
    }

    /**
     * The selected action is put into (or removed from) the localStorage and its visibility changes.
     * The state variable visibleTopbarActions keeps track of the visible actions to avoid  having to parse
     * the localStorage values every time we want to access them.
     * @param {TopbarAction} action
     */
    _setVisibility(actionId) {
        const actionIdStr = actionId.toString();
        if (this.state.topbarInfos.visibleTopbarActions[actionIdStr]) {
            delete this.state.topbarInfos.visibleTopbarActions[actionIdStr];
        } else {
            this.state.topbarInfos.visibleTopbarActions[actionIdStr] = true;
        }
        browser.localStorage.setItem(
            this.topbarActionsVisibilityKey,
            JSON.stringify(this.state.topbarInfos.visibleTopbarActions)
        );
    }

    _onShareCheckboxChange() {
        this.state.topbarInfos.newActionIsShared = !this.state.topbarInfos.newActionIsShared;
    }

    /**
     * @param {Event} ev
     */
    async _saveNewAction(ev) {
        const {
            newActionName,
            newActionIsShared,
            topbarActions,
            currentTopbarAction,
            visibleTopbarActions,
        } = this.state.topbarInfos;
        if (!newActionName) {
            this.notificationService.add(_t("A name for your new action is required."), {
                type: "danger",
            });
            ev.stopPropagation();
            return this.newActionNameRef.el.focus();
        }
        const duplicateName = topbarActions.some(({ name }) => name === newActionName);
        if (duplicateName) {
            this.notificationService.add(_t("An action with the same name already exists."), {
                type: "danger",
            });
            ev.stopPropagation();
            return this.newActionNameRef.el.focus();
        }
        const userId = newActionIsShared ? false : user.userId;

        const extractValues = ({ parent_action_id, action_id, parent_res_model }) => ({
            parent_action_id: parent_action_id[0],
            action_id: action_id ? action_id[0] : this.env.config.actionId,
            parent_res_model,
            parent_res_id: this.env.searchModel.globalContext.active_id,
            user_id: userId,
            is_deletable: true,
            default_view_mode: this.env.config.viewType,
        });
        const { parent_action_id, action_id, python_action, domain, context } = currentTopbarAction;
        const parentActionIdTuple = parent_action_id;
        const actionIdTuple = action_id;
        const values = {
            ...extractValues(currentTopbarAction),
            python_action,
            domain,
            context,
            name: newActionName,
        };
        const topbarActionId = await this.orm.create("ir.actions.topbar", [values]);
        const description = `${newActionName} Filter`;
        this.env.searchModel.createNewFavorite({
            description,
            isDefault: true,
            isShared: userId,
            topbarActionId: topbarActionId[0],
        });
        Object.assign(this.state.topbarInfos, {
            newActionName: "",
            newActionIsShared: false,
        });
        const enrichedNewTopbarAction = {
            ...values,
            parent_action_id: parentActionIdTuple,
            action_id: actionIdTuple,
            id: topbarActionId[0],
        };
        this.state.topbarInfos.topbarActions.push(enrichedNewTopbarAction);
        const topbarActionIdStr = topbarActionId[0].toString();
        visibleTopbarActions[topbarActionIdStr] = true;
        const order = this.state.topbarInfos.topbarActions.map((el) => el.id);
        browser.localStorage.setItem(
            this.topbarActionsVisibilityKey,
            JSON.stringify(visibleTopbarActions)
        );
        browser.localStorage.setItem(this.topbarOrderKey, JSON.stringify(order));
        this.env.config.setCurrentTopbarAction(topbarActionId[0]);
        this.state.topbarInfos.currentTopbarAction = enrichedNewTopbarAction;
        this.state.topbarInfos.newActionName = _t(`${newActionName} Custom`);
    }

    /**
     * @param {TopbarAction} action
     */
    openConfirmationDialog(action) {
        const dialogProps = {
            title: _t("Warning"),
            body: action.user_id
                ? _t("Are you sure that you want to remove this topbar action?")
                : _t("This topbar action is global and will be removed for everyone."),
            confirmLabel: _t("Delete"),
            confirm: async () => await this._deleteTopbarAction(action),
            cancel: () => {},
        };
        this.dialogService.add(ConfirmationDialog, dialogProps);
    }

    /**
     * @param {TopbarAction} action
     */
    async _deleteTopbarAction(action) {
        const { visibleTopbarActions, topbarActions, currentTopbarAction } = this.state.topbarInfos;
        const actionIdStr = action.id.toString();
        if (visibleTopbarActions[actionIdStr]) {
            delete visibleTopbarActions[actionIdStr];
        }
        browser.localStorage.setItem(
            this.topbarActionsVisibilityKey,
            JSON.stringify(visibleTopbarActions)
        );
        this.state.topbarInfos.topbarActions = topbarActions.filter(({ id }) => id !== action.id);
        await this.orm.unlink("ir.actions.topbar", [action.id]);
        if (action.id === currentTopbarAction?.id) {
            const { active_id, active_model } = this.env.searchModel.globalContext;
            const actionContext = action.context ? makeContext([action.context]) : {};
            const additionalContext = {
                ...actionContext,
                active_id,
                active_model,
                parent_action_id: action.parent_action_id[0],
            };
            this.actionService.doAction(action.parent_action_id[0], {
                additionalContext,
                stackPosition: "replaceCurrentAction",
            });
        }
    }

    /**
     * @param {TopbarAction} action
     */
    async onTopbarActionClick(action) {
        this.env.config.setTopbarActions(this.state.topbarInfos.topbarActions);
        const { active_id, active_model } = this.env.searchModel.globalContext;
        const actionContext = action.context ? makeContext([action.context]) : {};
        const context = {
            ...actionContext,
            active_id,
            active_model,
            current_topbar_action_id: action.id,
            parent_action_topbar_actions: this.state.topbarInfos.topbarActions,
            parent_action_id: action.parent_action_id[0],
        };
        this.actionService.doActionButton({
            type: action.python_action ? "object" : "action",
            resId: this.env.searchModel?.globalContext.active_id,
            name: action.python_action || action.action_id[0] || action.action_id,
            resModel: action.parent_res_model,
            context,
            stackPosition: this.env.config.parentActionId ? "replaceCurrentAction" : "",
            viewType: action.default_view_mode,
        });
    }

    /**
     * @param {number[]} order
     */
    _sortTopbarActions(order) {
        this.state.topbarInfos.topbarActions = this.state.topbarInfos.topbarActions.sort((a, b) => {
            if (!order.indexOf(a.id)) {
                return -1;
            }
            if (!order.indexOf(b.id)) {
                return 1;
            }
            return order.indexOf(a.id) - order.indexOf(b.id);
        });
    }

    /**
     * @param {Object} params
     * @param {HTMLElement} params.element
     */
    _sortTopbarActionStart({ element, addClass }) {
        addClass(element, "o_dragged_topbar_action");
    }

    /**
     * @param {Object} params
     * @param {HTMLElement} params.element
     * @param {HTMLElement} params.previous
     */
    _sortTopbarActionDrop({ element, previous }) {
        const order = this.state.topbarInfos.topbarActions.map((el) => el.id);
        const elementId = Number(element.dataset.id);
        const elementIndex = order.indexOf(elementId);
        order.splice(elementIndex, 1);
        if (previous) {
            const prevIndex = order.indexOf(Number(previous.dataset.id));
            order.splice(prevIndex + 1, 0, elementId);
        } else {
            order.splice(0, 0, elementId);
        }
        this._sortTopbarActions(order);
        browser.localStorage.setItem(this.topbarOrderKey, JSON.stringify(order));
    }
}

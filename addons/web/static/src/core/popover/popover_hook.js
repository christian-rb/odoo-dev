import { useService } from "@web/core/utils/hooks";

import { Component, onWillUnmount, status, useComponent, xml } from "@odoo/owl";
import { pick } from "../utils/objects";
import { Dialog } from "../dialog/dialog";

/**
 * @typedef PopoverHookReturnType
 * @property {(target: string | HTMLElement, props: object) => void} open
 *  - Signals the manager to open the configured popover
 *    component on the target, with the given props.
 * @property {() => void} close
 *  - Signals the manager to remove the popover.
 * @property {boolean} isOpen
 *  - Whether the popover is currently open.
 */

/**
 * @param {import("@web/core/popover/popover_service").PopoverServiceAddFunction} addFn
 * @param {typeof import("@odoo/owl").Component} component
 * @param {import("@web/core/popover/popover_service").PopoverServiceAddOptions} options
 * @returns {PopoverHookReturnType}
 */
export function makePopover(addFn, component, options) {
    let removeFn = null;
    function close() {
        removeFn?.();
    }
    return {
        open(target, props) {
            close();
            const newOptions = Object.create(options);
            newOptions.onClose = () => {
                removeFn = null;
                options.onClose?.();
            };
            removeFn = addFn(target, component, props, newOptions);
        },
        close,
        get isOpen() {
            return Boolean(removeFn);
        },
    };
}

/**
 * Manages a component to be used as a popover.
 *
 * @param {typeof import("@odoo/owl").Component} component
 * @param {import("@web/core/popover/popover_service").PopoverServiceAddOptions} [options]
 * @returns {PopoverHookReturnType}
 */
export function usePopover(component, options = {}) {
    const popoverService = useService("popover");
    const owner = useComponent();
    const newOptions = Object.create(options);
    newOptions.onClose = () => {
        if (status(owner) !== "destroyed") {
            options.onClose?.();
        }
    };
    const popover = makePopover(popoverService.add, component, newOptions);
    onWillUnmount(popover.close);
    return popover;
}

class PopoverAsDialog extends Component {
    static components = { Dialog };
    static props = ["close", "component", "componentProps"];
    static template = xml`
        <Dialog footer="false">
            <t t-component="props.component" t-props="componentProps"/>
        </Dialog>
    `;
    get componentProps() {
        return { ...this.props.componentProps, close: this.props.close };
    }
}

/**
 * Manages a component to be used as a popover.
 * Replaced by a fullscreen dialog on small screens.
 *
 * @param {typeof import("@odoo/owl").Component} component
 * @param {import("@web/core/popover/popover_service").PopoverServiceAddOptions} [options]
 * @returns {PopoverHookReturnType}
 */
export function useResponsivePopover(component, options = {}) {
    const popover = usePopover(...arguments);

    const dialogService = useService("dialog");
    const owner = useComponent();
    const newOptions = Object.create(options);
    newOptions.onClose = () => {
        if (status(owner) !== "destroyed") {
            options.onClose?.();
        }
    };
    const popoverAsDialog = makePopover(
        (_, comp, props, options) => {
            const wrapperProps = { component, componentProps: props };
            return dialogService.add(comp, wrapperProps, options);
        },
        PopoverAsDialog,
        pick(newOptions, "onClose")
    );
    onWillUnmount(popoverAsDialog.close);

    const getResponsive = () => (owner.env.isSmall ? popoverAsDialog : popover);
    return {
        get open() {
            return getResponsive().open;
        },
        get close() {
            return getResponsive().close;
        },
        get isOpen() {
            return getResponsive().isOpen;
        },
    };
}

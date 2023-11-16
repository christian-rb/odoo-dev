import { useService } from "@web/core/utils/hooks";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { browser } from "@web/core/browser/browser";
import { queryAll, queryOne } from "@odoo/hoot-dom";
import { Component, useState, useExternalListener } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

export class TourRecorderError extends Error {}

const PRECISE_IDENTIFIERS = ["data-menu-xmlid", "name", "contenteditable"];
const ODOO_CLASS_REGEX = /^oe?(-|_)[\w-]+$/;

/**
 * @param {Element[]} paths
 * @returns {string}
 */
const getShortestPredicate = (paths) => {
    let currentElem = paths.shift();
    let filteredPath = [];
    while (currentElem && queryAll(filteredPath.join(" > ")).length !== 1) {
        if (currentElem.parentElement.contentEditable === "true") {
            currentElem = paths.shift();
        }

        const odooClass = [...currentElem.classList].find((c) => ODOO_CLASS_REGEX.test(c));
        let currentPredicate = odooClass ? `.${odooClass}` : currentElem.tagName.toLowerCase();

        // If we are inside a link or button the previous elements, like <i></i>, <span></span>, etc., can be removed
        if (["BUTTON", "A"].includes(currentElem.tagName)) {
            filteredPath = [];
        }

        PRECISE_IDENTIFIERS.forEach((identifier) => {
            const identifierValue = currentElem.getAttribute(identifier);
            if (identifierValue) {
                currentPredicate += `[${identifier}='${identifierValue}']`;
            }
        });

        const siblingNodes = currentElem.parentElement.querySelectorAll(
            ":scope > " + currentPredicate
        );
        if (siblingNodes.length > 1) {
            currentPredicate += `:nth-child(${
                [...currentElem.parentElement.children].indexOf(currentElem) + 1
            })`;
        }

        filteredPath.unshift(currentPredicate);
        currentElem = paths.shift();
    }

    if (filteredPath.length > 2) {
        return reducePath(filteredPath);
    }

    return filteredPath.join(" > ");
};

/**
 * @param {string[]} paths
 * @returns {string}
 */
const reducePath = (paths) => {
    const numberOfElement = paths.length - 2;
    let currentElement = "";
    let hasReduced = false;
    let path = paths.shift();
    for (let i = 0; i < numberOfElement; i++) {
        currentElement = paths.shift();
        if (queryAll(`${path} ${paths.join(" > ")}`).length === 1) {
            hasReduced = true;
        } else {
            path += `${hasReduced ? " " : " > "}${currentElement}`;
            hasReduced = false;
        }
    }
    path += `${hasReduced ? " " : " > "}${paths.shift()}`;
    return path;
};

export class TourRecorder extends Component {
    static template = "web_tour_recorder.TourRecorder";
    static components = { Dropdown, DropdownItem };
    static props = {};
    static defaultState = {
        recording: false,
        url: "",
        lastStepIsInput: false,
        tourName: "",
    };

    setup() {
        this.startingEventPath = false;
        this.tourRecorderService = useService("tour_recorder");
        this.notification = useService("notification");
        this.state = useState({
            ...TourRecorder.defaultState,
            steps: [],
            collapsed: true,
        });

        useExternalListener(document, "pointerdown", this.setStartingEvent, { capture: true });
        useExternalListener(document, "pointerup", this.recordClickEvent, { capture: true });
        useExternalListener(document, "keyup", this.recordKeyboardEvent, { capture: true });
    }

    /**
     * @param {PointerEvent} ev
     */
    setStartingEvent(ev) {
        if (this.state.recording && !ev.target.closest(".o_tour_recorder")) {
            this.startingEventPath = ev.composedPath().filter((p) => p instanceof Element);
        }
    }

    /**
     * @param {PointerEvent} ev
     */
    recordClickEvent(ev) {
        if (this.state.recording && !ev.target.closest(".o_tour_recorder")) {
            const pathElements = ev.composedPath().filter((p) => p instanceof Element);
            this.addTourStep([...pathElements]);
            if (pathElements.join(" > ") !== this.startingEventPath.join(" > ")) {
                const lastStepInput = this.state.steps.at(-1);
                lastStepInput.run = `drag_and_drop_native ${lastStepInput.trigger}`;
                lastStepInput.trigger = this._getShortestPredicate(this.startingEventPath);
            }
        }
    }

    recordKeyboardEvent() {
        if (this.state.recording && this.state.lastStepIsInput) {
            const lastStepInput = this.state.steps.at(-1);
            const input = queryOne(lastStepInput.trigger);
            if (input.contentEditable === "true") {
                lastStepInput.run = `editor ${input.textContent}`;
            } else {
                lastStepInput.run = `edit ${input.value}`;
            }
        }
    }

    toggleRecording() {
        this.state.recording = !this.state.recording;
        this.state.lastStepIsInput = false;
        if (this.state.recording && !this.state.url) {
            this.state.url = browser.location.pathname + browser.location.search;
        }
    }

    saveTour() {
        const newTour = {
            name: this.state.tourName.replaceAll(" ", "_"),
            url: this.state.url,
            steps: this.state.steps.filter((s) => !s.triggerNotUnique),
            test: true,
        };

        try {
            this.tourRecorderService.addCustomTour(newTour);
            this.notification.add(_t("Custom tour '%s' added", newTour.name), { type: "success" });
            this.resetTourRecorderState();
        } catch (err) {
            if (err instanceof TourRecorderError) {
                this.notification.add(err.message, { type: "danger" });
            }
        }
    }

    resetTourRecorderState() {
        Object.assign(this.state, { ...TourRecorder.defaultState, steps: [] });
    }

    /**
     * @param {Element[]} paths
     */
    addTourStep(paths) {
        const shortestPath = getShortestPredicate(paths);
        if (queryAll(shortestPath).length !== 1) {
            this.notification.add(
                _t("A step couldn't find a unique path for a step. Please check the steps."),
                { type: "danger" }
            );
            this.state.steps.push({
                trigger: shortestPath,
                triggerNotUnique: true,
            });
        } else {
            const target = queryOne(shortestPath);
            this.state.lastStepIsInput =
                (!target.matches(":disabled") && ["TEXTAREA", "INPUT"].includes(target.tagName)) ||
                target.contentEditable === "true";
            this.state.steps.push({
                trigger: shortestPath,
            });
        }
    }
}

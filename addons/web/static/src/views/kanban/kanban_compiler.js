import { append, createElement, getTag } from "@web/core/utils/xml";
import { archParseBoolean } from "@web/views/utils";
import { ViewCompiler } from "@web/views/view_compiler";

const SPECIAL_TYPES = ["edit", "delete", "archive", "unarchive", "set_cover"];

export class KanbanCompiler extends ViewCompiler {
    setup() {
        this.compilers.push({
            selector: "kanban",
            fn: this.compileKanban,
            doNotCopyAttributes: true,
        });
    }

    //-----------------------------------------------------------------------------
    // Compilers
    //-----------------------------------------------------------------------------

    compileKanban(el, params) {
        const cardEls = [...el.childNodes].filter((c) => getTag(c) === "card");
        if (cardEls.length !== 1) {
            throw new Error("a kanban arch must have one (and only one) <card> child");
        }
        const cardEl = cardEls[0];
        let asideNode;
        let asidePosition;
        let mainNode;
        const card = createElement("div");
        for (const child of cardEl.childNodes) {
            switch (getTag(child)) {
                case "card-aside": {
                    asidePosition = child.getAttribute("position") || "start";
                    child.removeAttribute("position");
                    asideNode = this.compileAside(child, params);
                    break;
                }
                case "card-group":
                case "card-header":
                case "card-footer": {
                    if (!mainNode) {
                        mainNode = createElement("div");
                        mainNode.setAttribute(
                            "class",
                            "o_kanban_card_main d-flex flex-column justify-content-between gap-2 w-100 h-100"
                        );
                    }
                    append(mainNode, this.compileGroup(child, params));
                    break;
                }
                case "menu": {
                    append(card, this.compileMenu(child, params));
                    break;
                }
                default: {
                    append(card, this.compileNode(child, params));
                    break;
                }
            }
        }
        const cardClass = cardEl.getAttribute("class") || "";
        card.setAttribute("class", `w-100${asideNode ? " d-flex flex-row" : ""} ${cardClass}`);
        if (asideNode && asidePosition === "start") {
            append(card, asideNode);
        }
        if (mainNode) {
            append(card, mainNode);
        }
        if (asideNode && asidePosition === "end") {
            append(card, asideNode);
        }
        return card;
    }

    compileAside(el, params) {
        const aside = createElement("div");
        const elClass = el.getAttribute("class") || "";
        let asideClass = `o_kanban_aside d-block ${elClass}`;
        if (archParseBoolean(el.getAttribute("full"), false)) {
            asideClass += " o_kanban_aside_full";
        }
        aside.setAttribute("class", asideClass);
        for (const child of el.childNodes) {
            append(aside, this.compileNode(child, params));
        }
        return aside;
    }

    compileGroup(el, params) {
        const group = createElement("div");
        const elClass = el.getAttribute("class") || "";
        const type = getTag(el);
        let groupClass = `d-flex justify-content-between overflow-hidden d-empty-none ${elClass}`;
        if (type === "card-group") {
            groupClass += " flex-column o_kanban_card_group";
        } else {
            groupClass += ` flex-row align-items-end o_kanban_card_${type === "card-header" ? "header" : "footer"}`;
        }
        group.setAttribute("class", groupClass);
        for (const child of el.childNodes) {
            append(group, this.compileNode(child, params));
        }
        return group;
    }

    compileMenu(el, params) {
        const menu = createElement("KanbanRecordMenu");
        for (const child of el.childNodes) {
            append(menu, this.compileNode(child, params));
        }
        return menu;
    }

    /**
     * @override
     */
    compileButton(el, params) {
        const type = el.getAttribute("type");
        if (!SPECIAL_TYPES.includes(type)) {
            return super.compileButton(el, params);
        }

        const compiled = createElement(el.nodeName);
        for (const { name, value } of el.attributes) {
            compiled.setAttribute(name, value);
        }
        if (type === "delete") {
            compiled.setAttribute("t-if", "__comp__.canDelete");
        } else {
            compiled.setAttribute("t-if", "__comp__.canEdit");
        }
        compiled.setAttribute("t-on-click", `(ev) => __comp__.triggerAction("${type}", ev)`);
        if (getTag(el, true) === "a" && !compiled.hasAttribute("href")) {
            compiled.setAttribute("href", "#");
        }
        for (const child of el.childNodes) {
            append(compiled, this.compileNode(child, params));
        }

        return compiled;
    }

    /**
     * @override
     */
    compileField(el, params) {
        let compiled;
        const recordExpr = params.recordExpr || "__comp__.props.record";
        const dataPointIdExpr = params.dataPointIdExpr || `${recordExpr}.id`;
        if (!el.hasAttribute("widget")) {
            // fields without a specified widget are rendered as simple spans in kanban records
            const fieldId = el.getAttribute("field_id");
            compiled = createElement("span", {
                "t-out": params.formattedValueExpr || `__comp__.getFormattedValue("${fieldId}")`,
            });
        } else {
            compiled = super.compileField(el, params);
            const fieldId = el.getAttribute("field_id");
            compiled.setAttribute("id", `'${fieldId}_' + ${dataPointIdExpr}`);
            // In x2many kanban, records can be edited in a dialog. The same record as the one of
            // the kanban is used for the form view dialog, so its mode is switched to "edit", but
            // we don't want to see it in edition in the background. For that reason, we force its
            // fields to be readonly when the record is in edition, i.e. when it is opened in a form
            // view dialog.
            const readonlyAttr = compiled.getAttribute("readonly");
            if (readonlyAttr) {
                compiled.setAttribute("readonly", `${recordExpr}.isInEdition || (${readonlyAttr})`);
            } else {
                compiled.setAttribute("readonly", `${recordExpr}.isInEdition`);
            }
        }
        return compiled;
    }
}

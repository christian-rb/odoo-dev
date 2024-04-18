import { groupBy } from "@web/core/utils/arrays";
import { append, combineAttributes, createElement, getTag } from "@web/core/utils/xml";
import { archParseBoolean } from "@web/views/utils";
import { ViewCompiler } from "@web/views/view_compiler";

const SPECIAL_TYPES = ["edit", "delete", "archive", "unarchive", "set_cover"];

const ITEMS_TO_TAG = {
    group: "section",
    title: "header",
    footer: "footer",
};

export class KanbanCompiler extends ViewCompiler {
    setup() {
        this.compilers.push(
            {
                selector: "kanban",
                fn: this.compileKanban,
                doNotCopyAttributes: true,
            },
            { selector: "group, title, footer", fn: this.compileGroup }
        );
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
        const card = createElement("article");
        card.setAttribute("t-att-class", "__comp__.rootClass");
        card.setAttribute("t-att-data-id", "__comp__.props.record.id");
        card.setAttribute("t-att-tabindex", "__comp__.props.record.model.useSampleModel ? -1 : 0");
        let asideNode;
        let asidePosition;
        let mainNode;
        for (const child of cardEl.childNodes) {
            switch (getTag(child)) {
                case "aside": {
                    asidePosition = child.getAttribute("position") || "start";
                    asideNode = this.compileAside(child, params);
                    break;
                }
                case "group":
                case "title":
                case "footer": {
                    if (!mainNode) {
                        mainNode = createElement("main");
                        mainNode.setAttribute("class", "o_kanban_card_main");
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
        if (asideNode && asidePosition === "start") {
            append(card, asideNode);
        }
        if (mainNode) {
            append(card, mainNode);
        }
        if (asideNode && asidePosition === "end") {
            append(card, asideNode);
        }
        if (asideNode || mainNode) {
            const direction = cardEl.getAttribute("direction");
            if (direction === "column") {
                combineAttributes(card, "class", " o_kanban_card_column", " + ");
            }
        }
        return card;
    }

    compileAside(el, params) {
        const aside = createElement("aside");
        const elClass = el.getAttribute("class") || "";
        let asideClass = `o_kanban_card_aside o_kanban_card_item ${elClass}`;
        if (archParseBoolean(el.getAttribute("full"), false)) {
            asideClass += " o_kanban_card_aside_full";
        } else {
            asideClass += " o_kanban_card_aside_contained";
        }
        aside.setAttribute("class", asideClass);
        aside.classList.toggle("o_kanban_aside_end", el.getAttribute("position") == "end");

        for (const child of el.childNodes) {
            append(aside, this.compileNode(child, params));
        }
        return aside;
    }

    compileGroup(el, params) {
        const type = getTag(el);
        const tagName = ITEMS_TO_TAG[type];
        const group = createElement(tagName);
        const direction = el.getAttribute("direction") || "column";
        let groupClass = `${
            el.getAttribute("class") || ""
        } o_kanban_card_item o_kanban_card_${type}`;
        if (type === "group" && direction === "row") {
            groupClass += " o_kanban_card_group_row";
        }
        group.setAttribute("class", groupClass);

        // move right aligned elements to the right
        let childNodes = [...el.childNodes];
        if (direction === "column" || ["foot", "head"].includes(type)) {
            const { left, right } = groupBy(childNodes, (n) => {
                return n.classList?.contains("o_card_align_end") ? "right" : "left";
            });
            childNodes = [left || [], right || []].flat();
        }

        for (const child of childNodes) {
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

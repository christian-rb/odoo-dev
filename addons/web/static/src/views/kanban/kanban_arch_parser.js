import { extractAttributes, visitXML } from "@web/core/utils/xml";
import { stringToOrderBy } from "@web/search/utils/order_by";
import { Field } from "@web/views/fields/field";
import { Widget } from "@web/views/widgets/widget";
import { archParseBoolean, getActiveActions, processButton } from "@web/views/utils";

export class KanbanArchParser {
    parse(xmlDoc, models, modelName) {
        const fields = models[modelName].fields;
        const className = xmlDoc.getAttribute("class") || null;
        const allowGlobalClick = archParseBoolean(xmlDoc.getAttribute("global_click"), true);
        const cardColorField = xmlDoc.getAttribute("color") || false;
        let defaultOrder = stringToOrderBy(xmlDoc.getAttribute("default_order") || null);
        const defaultGroupBy = xmlDoc.getAttribute("default_group_by");
        const limit = xmlDoc.getAttribute("limit");
        const countLimit = xmlDoc.getAttribute("count_limit");
        const recordsDraggable = archParseBoolean(xmlDoc.getAttribute("records_draggable"), true);
        const groupsDraggable = archParseBoolean(xmlDoc.getAttribute("groups_draggable"), true);
        const activeActions = getActiveActions(xmlDoc);
        activeActions.archiveGroup = archParseBoolean(xmlDoc.getAttribute("archivable"), true);
        activeActions.createGroup = archParseBoolean(xmlDoc.getAttribute("group_create"), true);
        activeActions.deleteGroup = archParseBoolean(xmlDoc.getAttribute("group_delete"), true);
        activeActions.editGroup = archParseBoolean(xmlDoc.getAttribute("group_edit"), true);
        activeActions.quickCreate =
            activeActions.create && archParseBoolean(xmlDoc.getAttribute("quick_create"), true);
        const onCreate = xmlDoc.getAttribute("on_create");
        const quickCreateView = xmlDoc.getAttribute("quick_create_view");
        const tooltipInfo = {};
        let handleField = null;
        const fieldNodes = {};
        const fieldNextIds = {};
        const widgetNodes = {};
        let widgetNextId = 0;
        const jsClass = xmlDoc.getAttribute("js_class");
        const action = xmlDoc.getAttribute("action");
        const type = xmlDoc.getAttribute("type");
        const openAction = action && type ? { action, type } : null;
        let headerButtons = [];
        const creates = [];
        let button_id = 0;
        let cardClassName;
        // Root level of the template
        visitXML(xmlDoc, (node) => {
            if (node.tagName === "header") {
                headerButtons = [...node.children]
                    .filter((node) => node.tagName === "button")
                    .map((node) => ({
                        ...processButton(node),
                        type: "button",
                        id: button_id++,
                    }))
                    .filter((button) => button.invisible !== "True" && button.invisible !== "1");
                return false;
            } else if (node.tagName === "control") {
                for (const childNode of node.children) {
                    if (childNode.tagName === "button") {
                        creates.push({
                            type: "button",
                            ...processButton(childNode),
                        });
                    } else if (childNode.tagName === "create") {
                        creates.push({
                            type: "create",
                            context: childNode.getAttribute("context"),
                            string: childNode.getAttribute("string"),
                        });
                    }
                }
                return false;
            }
            // Case: field node
            if (node.tagName === "field") {
                const fieldInfo = Field.parseFieldNode(node, models, modelName, "kanban", jsClass);
                const name = fieldInfo.name;
                if (!(fieldInfo.name in fieldNextIds)) {
                    fieldNextIds[fieldInfo.name] = 0;
                }
                const fieldId = `${fieldInfo.name}_${fieldNextIds[fieldInfo.name]++}`;
                fieldNodes[fieldId] = fieldInfo;
                node.setAttribute("field_id", fieldId);
                if (fieldInfo.options.group_by_tooltip) {
                    tooltipInfo[name] = fieldInfo.options.group_by_tooltip;
                }
                if (fieldInfo.isHandle) {
                    handleField = name;
                }
            }
            if (node.tagName === "widget") {
                const widgetInfo = Widget.parseWidgetNode(node);
                const widgetId = `widget_${++widgetNextId}`;
                widgetNodes[widgetId] = widgetInfo;
                node.setAttribute("widget_id", widgetId);
            }
            if (node.tagName === "card") {
                cardClassName = node.getAttribute("class") || null;
            }
        });

        // Progressbar
        let progressAttributes = false;
        const progressBar = xmlDoc.querySelector("progressbar");
        if (progressBar) {
            progressAttributes = this.parseProgressBar(progressBar, fields);
        }

        if (!defaultOrder.length && handleField) {
            defaultOrder = stringToOrderBy(handleField);
        }

        return {
            activeActions,
            allowGlobalClick,
            cardClassName,
            className,
            creates,
            defaultGroupBy,
            fieldNodes,
            widgetNodes,
            handleField,
            headerButtons,
            defaultOrder,
            onCreate,
            openAction,
            quickCreateView,
            recordsDraggable,
            groupsDraggable,
            limit: limit && parseInt(limit, 10),
            countLimit: countLimit && parseInt(countLimit, 10),
            progressAttributes,
            cardColorField,
            tooltipInfo,
            examples: xmlDoc.getAttribute("examples"),
            xmlDoc,
        };
    }

    parseProgressBar(progressBar, fields) {
        const attrs = extractAttributes(progressBar, ["field", "colors", "sum_field", "help"]);
        return {
            fieldName: attrs.field,
            colors: JSON.parse(attrs.colors),
            sumField: fields[attrs.sum_field] || false,
            help: attrs.help,
        };
    }
}

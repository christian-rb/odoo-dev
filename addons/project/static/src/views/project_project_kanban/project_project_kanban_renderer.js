/** @odoo-module */

import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { ProjectProjectKanbanHeader } from "./project_project_kanban_header";
import { onWillStart } from "@odoo/owl";
import { user } from "@web/core/user";


export class ProjectProjectKanbanRenderer extends KanbanRenderer {
    static components = {
        ...KanbanRenderer.components,
        KanbanHeader: ProjectProjectKanbanHeader,
    };

    setup() {
        super.setup();
        onWillStart(async () => {
            this.isProjectManager = await user.hasGroup('project.group_project_manager');
        });
    }

    get canResequenceGroups() {
        return super.canResequenceGroups && this.isProjectManager;
    }
}

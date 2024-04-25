/** @odoo-module **/

import { registry } from "@web/core/registry";
import { activityView } from "@mail/views/web/activity/activity_view";
import { ProjectControlPanel } from "@project/components/project_control_panel/project_control_panel";
import { ProjectActivityRenderer } from "./project_activity_renderer";

export const projectActivityView = {
    ...activityView,
    ControlPanel: ProjectControlPanel,
    Renderer: ProjectActivityRenderer,
};
registry.category("views").add("project_activity", projectActivityView);

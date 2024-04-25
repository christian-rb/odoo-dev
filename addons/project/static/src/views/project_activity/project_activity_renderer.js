import { ActivityRenderer } from "@mail/views/web/activity/activity_renderer";
import { onWillStart } from "@odoo/owl";
import { user } from "@web/core/user";

export class ProjectActivityRenderer extends ActivityRenderer {
    static template = "project.projectActivityRenderer";

    setup() {
        super.setup();
        onWillStart(async () => {
            this.isProjectManager = await user.hasGroup('project.group_project_manager');
        });
    }
}
import { RelationalModel } from "@web/model/relational_model/relational_model";

export class ProjectUpdateFormModel extends RelationalModel {
    static services = [...RelationalModel.services, "project_update_date_filter"];

    setup(params, { project_update_date_filter }) {
        this.projectUpdateDateFilter = project_update_date_filter;
        super.setup(...arguments);
    }

    /**
     * @override
     */
    async _loadNewRecord(config, params = {}) {
        Object.assign(config.context, this.projectUpdateDateFilter.dates);
        return super._loadNewRecord(config, params);
    }
}

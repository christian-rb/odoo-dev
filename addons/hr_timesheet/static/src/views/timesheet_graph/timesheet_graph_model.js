/** @odoo-module **/

import { ProjectTaskGraphModel } from "@project/views/project_task_graph/project_task_graph_model";
import { HOURS_MEASURE_FIELDS } from "@web/views/graph/graph_renderer";

export class hrTimesheetGraphModel extends ProjectTaskGraphModel {
    /**
     * @override
     */
    setup(params, services) {
        super.setup(...arguments);
        this.companyService = services.company;
    }

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Override processDataPoints to take into account the analytic line uom.
     * @override
     */
    _getProcessedDataPoints() {
        const currentCompany = this.companyService.currentCompany;
        const factor = currentCompany.timesheet_uom_factor || 1;
        if (factor !== 1 && HOURS_MEASURE_FIELDS.includes(this.metaData.measure)) {
            // recalculate the Duration values according to the timesheet_uom_factor
            for (const dataPt of this.dataPoints) {
                dataPt.value *= factor;
            }
        }
        return super._getProcessedDataPoints(...arguments);
    }
}
hrTimesheetGraphModel.services = [...ProjectTaskGraphModel.services, "company"];

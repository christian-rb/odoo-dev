import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { useService } from "@web/core/utils/hooks";

export class OpenWorkOrderFormWizard extends Component {
    static template = "mrp.openWorkOrderFormWizard";
    static props = { ...standardWidgetProps };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
    }

    showIcon() {
        if (this.env.model.config.resModel != "mrp.production") {
            return false;
        }
        return true;
    }

    async openWizard() {
        const actionResult = await this.orm.call('mrp.workorder', 'action_open_wizard', [this.props.record.resId]);
        return this.action.doAction(actionResult);
    }
}

export const openWorkOrderFormWizard = {
    component: OpenWorkOrderFormWizard,
};

registry.category("view_widgets").add("open_workorder_order_form_wizard", openWorkOrderFormWizard);

import { AccountX2ManyListController } from "@account/views/account_x2many_list/account_x2many_list_controller";
import { listView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";

const AccountX2ManyListView = {
    ...listView,
    Controller: AccountX2ManyListController,
};

registry.category("views").add("account_x2many_list", AccountX2ManyListView);

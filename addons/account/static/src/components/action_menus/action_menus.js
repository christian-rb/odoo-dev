import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";
import {ActionMenus} from "@web/search/action_menus/action_menus";


patch(ActionMenus.prototype, {

    async getPrintItems() {
        let printItems = await super.getPrintItems();
        if (this.props?.getActiveIds && this.props?.resModel === "account.move") {
            // Prepend the PDF button in the Print/Download menu
            return [
                {
                    description: _t("PDF"),
                    key: "action_invoice_download_pdf",
                },
                ...printItems,
            ];
        }
        return printItems;
    },

    async onItemSelected(item) {
        if (this.props.resModel === "account.move" && item.key === "action_invoice_download_pdf") {
            const moveIds = this.props.getActiveIds();
            const action = await this.orm.call("account.move", "action_invoice_download_pdf", [moveIds]);
            this.actionService.doAction(action);
            this.env.services.notification.add(_t("Downloading..."), {
                type: "info",
            });
        }
        return super.onItemSelected(item);
    },

});

import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { ActionMenus } from "@web/search/action_menus/action_menus";


patch(ActionMenus.prototype, {
    async getPrintItems() {
        const printItems = await super.getPrintItems();
        if (this.props?.getActiveIds && this.props?.resModel === "account.move") {
            // Adds an XML UBL button in the Print/Download menu if there is at least one
            // of the selected moves with an ubl xml linked.
            // This can't be done through classic action report since it's not a PDF.
            const moveIds = this.props.getActiveIds();
            const recMatch = await this.orm.search(
                this.props.resModel,
                [["id", "in", moveIds], ["ubl_cii_xml_file", "!=", false]],
                {limit: 1}
            );
            if (recMatch.length > 0) {
                printItems.push({
                    description: _t("XML UBL"),
                    key: "action_invoice_download_ubl",
                });
            }
        }
        return printItems;
    },

    async onItemSelected(item) {
        if (this.props.resModel === "account.move" && item.key === "action_invoice_download_ubl") {
            const moveIds = this.props.getActiveIds();
            const action = await this.orm.call("account.move", "action_invoice_download_ubl", [moveIds]);
            return this.actionService.doAction(action);
        }
        super.onItemSelected(item);
    }
});

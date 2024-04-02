/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from '@web/core/registry';
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { PartnerAutoCompleteMany2one, partnerAutoCompleteMany2one } from "@partner_autocomplete/js/partner_autocomplete_many2one";

export class PurchaseOrderVendorConformation extends PartnerAutoCompleteMany2one {
    setup() {
        super.setup();
    }

    async updateRecord(value) {
        super.updateRecord(value);
        if (this.props.record.data.order_line.records.length === 0) {
            return;
        }
        await this.showConfirmationDialog();
    }
    
    async showConfirmationDialog() {
        return new Promise(resolve => {
            this.dialog.add(ConfirmationDialog, {
                title: _t("Update Lines?"),
                body: _t("Do you want to update lines based on the new vendor selected?"),
                confirm: async () => {
                    const orderLineRecords = this.props.record.data.order_line.records;
                    await Promise.all(orderLineRecords.map(record => (
                        record.update({'manual_set': false, 'price_unit': 0}),
                        record.update({'product_qty': record.data.product_qty})
                    )
                    ));
                },
                cancel: () => resolve(false),
                confirmLabel: _t("Update"),
                cancelLabel: _t("Keep as is"),
            });
        });
    }  
}

export const purchaseVendorMany2OneField = {
    ...partnerAutoCompleteMany2one,
    component: PurchaseOrderVendorConformation,
};

registry.category("fields").add("purchase_vendor_many2one", purchaseVendorMany2OneField);

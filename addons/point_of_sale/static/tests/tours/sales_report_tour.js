/** @odoo-module */
import * as ProductScreen from "@point_of_sale/../tests/tours/utils/product_screen_util";
import * as PaymentScreen from "@point_of_sale/../tests/tours/utils/payment_screen_util";
import * as ReceiptScreen from "@point_of_sale/../tests/tours/utils/receipt_screen_util";
import * as Chrome from "@point_of_sale/../tests/tours/utils/chrome_util";
import * as Dialog from "@point_of_sale/../tests/tours/utils/dialog_util";

import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("SaleReportUITour", {
    test: true,
    steps: () =>
        [
            Dialog.confirm("Open session"),
            ProductScreen.clickDisplayedProduct("Desk Organizer", true, "1.0", "5.10"),
            ProductScreen.clickPayButton(),
            PaymentScreen.clickPaymentMethod("Cash"),
            PaymentScreen.enterPaymentLineAmount("Cash", "5.1", true, {
                amount: "5.10",
                remaining: "0.00",
                change: "0.00",
            }),
            PaymentScreen.clickValidate(),
            ReceiptScreen.isShown(),
            ReceiptScreen.clickNextOrder(),
            Chrome.clickMenuOption("Close Register"),
            Dialog.secondary("Daily Sale"),
            Dialog.confirm("Close Register"),
            Dialog.secondary("Proceed Anyway"),
        ].flat(),
});

/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.PortalInvoicePayment = publicWidget.Widget.extend({
    selector: '#o_portal_invoice_payment',

    start: function () {
        const params = new URLSearchParams(window.location.search);
        const showPaymentModal = params.get('showPaymentModal') === 'true';
        var button = document.getElementById('o_invoice_portal_pay_now_btn');
        if (showPaymentModal && button) {
            button.click();
        }
    },
})

export default publicWidget.registry.PortalInvoicePayment;

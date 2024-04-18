/** @odoo-module **/

import PaymentForm from '@payment/js/payment_form';
PaymentForm.include({
    _prepareTransactionRouteParams() {
        let transactionRouteParams = this._super(...arguments);
        let postParams = JSON.parse(pythonDictToJSON(this.paymentContext['postParams']));
        transactionRouteParams = { ...transactionRouteParams, ...postParams };
        return transactionRouteParams;
    },
});

function pythonDictToJSON(pythonDict) {
    if (!pythonDict) {
        return '{}';
    }

    return pythonDict
        .replace(/'/g, '"') //replaces all single quotes with double quotes
        .replace(/True/g, 'true') //replaces all Python boolean values to JS boolean values
        .replace(/False/g, 'false');
}

/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';
import { browser } from '@web/core/browser/browser';

publicWidget.registry.WebsiteSaleGiftCardCopy = publicWidget.Widget.extend({
    selector: '.o_purchased_gift_card',
    /**
     * @override
     */
    start: async function () {
        if (!browser.navigator.clipboard) {
            return browser.console.warn("This browser doesn't allow to copy to clipboard");
        }
        await browser.navigator.clipboard.writeText(this.$el.find('.copy-to-clipboard')[0].innerText);
    }
});

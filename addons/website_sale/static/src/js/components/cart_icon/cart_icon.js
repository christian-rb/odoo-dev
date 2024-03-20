/** @odoo-module **/

import { Component, useEffect, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class CartIcon extends Component {
    static template = "website_sale.cartIcon";

    setup() {
        this.websiteSaleService = useService("website_sale"); // TODO VCR hook on the service for quick information related to the cart
        this.websiteSaleContext = useState(this.websiteSaleService.context)


        useEffect( // TODO VCR add the class to grow the number when it changes
            () => {},
            () => [this.websiteSaleContext.nbItemsInCart]
        )
    }

}

registry.category("public_components").add("website_sale.CartIcon", CartIcon);

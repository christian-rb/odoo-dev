import { Component } from "@odoo/owl";
import { renderToElement } from "@web/core/utils/render";

export class SaleActionHelper extends Component {
    static template = "sale.SaleActionHelper";
    static props = ["noContentHelp"];

    openVideoPreview() {
        this.modal = renderToElement('sale.VideoPreview', {
            url: "https://www.youtube.com/embed/N4zw-2t6spk?autoplay=1"
        });
        document.body.append(this.modal);
        this.modal.addEventListener('hidden.bs.modal', () => {
            this.modal.remove();
        });
        const modal = new Modal(this.modal);
        modal.show();
    }
};

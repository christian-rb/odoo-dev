/** @odoo-module */

import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class TransferMergeDialog extends Component {
    static template = "pos_restaurant.TransferMergeDialog";
    static components = { Dialog };
    static props = {
        isTableToMerge: false,
        close: Function,
        tableTransfer: Function,
        mergeTable: Function,
    };

    closeDialog(){
        this.props.close();
    }

    merge(){
        this.props.mergeTable();
        this.props.close();
    }

    transfer(){
        this.props.tableTransfer();
        this.props.close();
    }
}

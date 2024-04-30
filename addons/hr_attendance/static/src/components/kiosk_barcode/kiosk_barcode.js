/** @odoo-module **/

import { BarcodeScanner } from "@barcodes/components/barcode_scanner";
import { AttendanceBarcodeDialog } from "../barcode_dialog/kiosk_barcode_dialog";
import { scanBarcode } from "@web/webclient/barcode/barcode_scanner";

export class KioskBarcodeScanner extends BarcodeScanner {
    static props = {
        ...BarcodeScanner.props,
        barcodeSource: String,
    };

    setup() {
        super.setup();
        this.scanBarcode = () => scanBarcode(this.env, this.facingMode, AttendanceBarcodeDialog);
    }

    get facingMode() {
        if (this.props.barcodeSource == "front") {
            return "user";
        }
        return super.facingMode;
    }
}

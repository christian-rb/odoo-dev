import { BarcodeDialog } from "@web/webclient/barcode/barcode_scanner";

export class AttendanceBarcodeDialog extends BarcodeDialog {
    /**
     * @override
     */
    get title() {
        return "Scan your badge's barcode";
    }
}
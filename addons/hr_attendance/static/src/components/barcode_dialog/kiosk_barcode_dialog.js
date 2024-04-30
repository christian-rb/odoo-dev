import { onWillStart } from "@odoo/owl";
import { BarcodeDialog } from "@web/webclient/barcode/barcode_scanner";
import { useService } from "@web/core/utils/hooks";
export class AttendanceBarcodeDialog extends BarcodeDialog {
    static template = "hr_attendance.BarcodeDialog";

    /**
     * @override
     */
    setup(){
        super.setup();
        this.orm = useService("orm");

        onWillStart( async () => {
            this.employeeNumber = await this.orm.searchCount('hr.employee', []);
            console.log(this.employeeNumber);
        });
    }

    /**
     * @override
     */
    get title() {
        return "Scan your badge's barcode";
    }
}

import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import ToursDialog from "@web_tour/debug/tour_dialog_component";
import { useState, useRef } from "@odoo/owl";
import { TourRecorderError } from "@web_tour_recorder/tour_recorder/tour_recorder";
import { downloadFile } from "@web/core/network/download";
import { _t } from "@web/core/l10n/translation";

/**
 * @typedef {import("@web_tour/tour_service/tour_service").Tour} Tour
 */

patch(ToursDialog, {
    components: { ...ToursDialog.components, Dropdown, DropdownItem },
});

patch(ToursDialog.prototype, {
    setup() {
        super.setup();
        this.tourRecorder = useService("tour_recorder");
        this.notification = useService("notification");
        this.state = useState({
            customTours: this.tourRecorder.getCustomTours(),
        });
        this.importTourInput = useRef("import_tour_input");
    },

    /**
     * @param {MouseEvent} ev
     */
    onStartCustomTour(ev) {
        this.tourRecorder.startCustomTour(ev.target.dataset.name, { mode: "manual" });
        this.props.close();
    },
    /**
     * @param {MouseEvent} ev
     */
    onTestCustomTour(ev) {
        this.tourRecorder.startCustomTour(ev.target.dataset.name, {
            mode: "auto",
            stepDelay: 500,
            showPointerDuration: 250,
        });
        this.props.close();
    },

    /**
     *
     * @param {Tour} customTour
     */
    deleteTour(customTour) {
        const tourIndex = this.state.customTours.indexOf(customTour);
        this.state.customTours.splice(tourIndex, 1);
        this.tourRecorder.removeCustomTour(customTour);
        this.notification.add(_t("Tour '%s' correctly deleted", customTour.name), {
            type: "success",
        });
    },

    /**
     * @param {InputEvent} ev
     */
    importTour(ev) {
        if (ev.target.files.length) {
            const file = ev.target.files[0];
            const reader = new FileReader();
            reader.readAsText(file, "UTF-8");
            reader.fileName = file.name.replaceAll(" ", "_");
            reader.onload = this.addTourFromFile.bind(this);
        }
    },

    /**
     * @param {Tour} tour
     */
    exportTourJSON(tour) {
        downloadFile(
            JSON.stringify({
                ...tour,
                wait_for: undefined,
                steps: tour.steps.map((s) => {
                    return {
                        ...s,
                        state: undefined,
                    };
                }),
            }),
            tour.name,
            "application/json"
        );
    },

    /**
     * @param {Tour} tour
     */
    exportTourJS(tour) {
        // Must pass by a variable because the JS interpolating is replacing the import statements
        const importStatement = "import { registry } from '@web/core/registry';";
        const JSstring = `${importStatement}

registry.category("web_tour.tours").add("${tour.name}", {
    url: "${tour.url}",
    steps: () => ${JSON.stringify(
        tour.steps.map((s) => {
            return {
                ...s,
                state: undefined,
            };
        }),
        null,
        4
    )},
});`;
        downloadFile(JSstring, tour.name, "application/javascript");
    },

    /**
     * @param {ProgressEvent<FileReader>} ev
     */
    addTourFromFile(ev) {
        const tourString = ev.target.result;
        const customTour = JSON.parse(tourString);
        customTour.name = ev.target.fileName.replace(".json", "");

        try {
            this.tourRecorder.addCustomTour(customTour);
            this.notification.add(_t("Custom tour '%s' added", customTour.name), {
                type: "success",
            });
            this.state.customTours = this.getCustomTours();
        } catch (err) {
            if (err instanceof TourRecorderError) {
                this.notification.add(err.message, { type: "danger" });
            }
        }
    },
});

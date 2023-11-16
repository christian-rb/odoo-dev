import { registry } from "@web/core/registry";
import { browser } from "@web/core/browser/browser";
import { TourRecorder, TourRecorderError } from "@web_tour_recorder/tour_recorder/tour_recorder";
import { _t } from "@web/core/l10n/translation";

/**
 * @typedef {import("@web_tour/tour_service/tour_service").TourStep} TourStep
 *
 * @typedef {{
 *  steps: TourStep[];
 *  name: string;
 *  url: string;
 *  test: boolean;
 * }} CustomTour
 */

const CUSTOM_TOURS_LOCAL_STORAGE_KEY = "custom_tours";

export const tourRecorderService = {
    dependencies: ["overlay", "tour_service"],
    start(_env, { overlay, tour_service }) {
        const customTours = getCustomTours();
        overlay.add(TourRecorder, {}, { sequence: 99999 });

        /**
         * @param {CustomTour} customTour
         */
        function addCustomTour(customTour) {
            const customTours = getCustomTours();
            if (customTours.some((t) => t.name === customTour.name)) {
                throw TourRecorderError(_t("Custom tour '%s' already exist!", customTour.name));
            } else {
                customTours.push(customTour);
                browser.localStorage.setItem(
                    CUSTOM_TOURS_LOCAL_STORAGE_KEY,
                    JSON.stringify(customTours)
                );
            }
        }

        /**
         * @param {CustomTour} tour
         */
        function removeCustomTour(tour) {
            let customTours = getCustomTours();
            customTours = customTours.filter((t) => t.name !== tour.name);
            browser.localStorage.setItem(
                CUSTOM_TOURS_LOCAL_STORAGE_KEY,
                JSON.stringify(customTours)
            );
        }

        /**
         * @returns {CustomTour[]}
         */
        function getCustomTours() {
            const customToursString = browser.localStorage.getItem(CUSTOM_TOURS_LOCAL_STORAGE_KEY);
            return JSON.parse(customToursString || "[]");
        }

        /**
         * @param {string} customTourName
         */
        function startCustomTour(customTourName, options) {
            const customTour = customTours.find((t) => t.name === customTourName);
            registry.category("web_tour.tours").add(customTour.name, {
                ...customTour,
                steps: () => customTour.steps,
            });
            tour_service.startTour(customTour.name, options);
        }

        return {
            addCustomTour,
            removeCustomTour,
            getCustomTours,
            startCustomTour,
        };
    },
};

registry.category("services").add("tour_recorder", tourRecorderService);

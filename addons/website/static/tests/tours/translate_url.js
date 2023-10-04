/** @odoo-module */

import wTourUtils from "@website/js/tours/tour_utils";

const translateUrl = function (newUrl, language) {
    return [{
        content: "Click on the translate button",
        trigger: "span.o_field_translate:contains('EN')",
    }, {
        content: "Change the translation of the contactus page url",
        trigger: `div.row:contains(${language}) input[type='text']`,
        run: `text ${newUrl}`,
    }, {
        content: "Click on 'Save'",
        trigger: ".modal-content:contains('Translate: url') footer button:contains('Save')",
    },
    ];
};


wTourUtils.registerWebsitePreviewTour("translate_url", {
    test: true,
    url: "/contactus",
}, () => [
    {
        content: "Click on the 'Site' button",
        trigger: "button:contains('Site')",
    }, {
        content: "Click on the 'Properties' button",
        trigger: "a:contains('Properties')",
    },
    ...translateUrl("/contactus-fr", "French"),
    ...translateUrl("/contactus", "French"),
    {
        content: "Wait for the load operation to finish",
        trigger: "span.o_field_translate:contains('EN')",
        isCheck: true,
    },
]);

wTourUtils.registerWebsitePreviewTour("update_homepage_url", {
    test: true,
    url: "/contactus",
}, () => [
    {
        content: "Click on the 'Site' button",
        trigger: "button:contains('Site')",
    }, {
        content: "Click on the 'Properties' button",
        trigger: "a:contains('Properties')",
    },
    ...translateUrl("/contactus-en", "English"),
    {
        content: "Wait for the load operation to finish",
        trigger: "span.o_field_translate:contains('EN')",
        isCheck: true,
    },
]);


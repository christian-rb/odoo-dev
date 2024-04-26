/** @odoo-module **/

import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("test_edit_event_from_calendar", {
    test: true,
    steps: () => [
        {
            content: "Enter event form",
            trigger: 'a[data-event-id="1"]',
            run: "dblclick",
        },
        {
            content: "Change the name of the form",
            trigger: "input#name_0",
            run: "text make your bed",
        },
        {
            content: "Return to calendar",
            trigger: ".o_back_button",
        },
        {
            content: "Move event to Wednesday 1.15 PM",
            trigger: 'a[data-event-id="1"]',
            run: 'drag_and_drop_native tr[data-time="13:30:00"] td.fc-widget-content:not(.fc-time)',
        },
    ],
});

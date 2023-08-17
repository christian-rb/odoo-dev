/** @odoo-module **/

import options from "@web_editor/js/editor/snippets.options";

options.registry.Alert = options.Class.extend({

    //--------------------------------------------------------------------------
    // Options
    //--------------------------------------------------------------------------

    /**
     * Changes alert's icon pictogram.
     *
     * @see this.selectClass for parameters
     */
    iconClass(previewMode, widgetValue, params) {
        const iconEl = this.$target[0].querySelector('.s_alert_icon');
        if (!iconEl) {
            return;
        }

        // Note: this function is basically a "selectClass" combined with an
        // "applyTo" but each option already comes with a "selectClass"
        // targeting the main container. This is also why this does not need
        // a _computeWidgetState, relying on the "selectClass" one which comes
        // afterwards alphabetically (compared to "iconClass").
        iconEl.classList.remove(...params.possibleValues.filter(v => !!v));
        iconEl.classList.add(widgetValue);
    },
});

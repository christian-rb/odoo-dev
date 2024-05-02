/** @odoo-module **/

import { FormRenderer } from '@web/views/form/form_renderer';
import { formView } from "@web/views/form/form_view";
import { registry } from "@web/core/registry";
import { startAuthentication } from "../lib/simplewebauthn.js"
import { useService } from "@web/core/utils/hooks";
import { onMounted } from "@odoo/owl";

export class PasskeyConditionalField extends FormRenderer {
    setup() {
        super.setup();
        this.rpc = useService("rpc")
        this.actionService = useService("action")

        if(this.props.archInfo.arch.startsWith("<form")) {
            onMounted(() => this.conditionalPasskey())
        }
    }

    async conditionalPasskey() {
        if(PasskeyConditionalField.runOnce) {
            return;
        }
        PasskeyConditionalField.runOnce = true

        try {
            const serverOptions = await this.rpc("/auth/passkey/start-auth")
            const auth = await startAuthentication(serverOptions, true)
            auth.verify_identity_id = this.props.record.evalContext.active_id
            const verification = await this.rpc("/auth/passkey/verify-auth", {auth: auth})
            if(verification.action) {
                this.actionService.doAction(verification.action)
            } else {
                this.actionService.loadState()
            }
        } catch (e) {
            console.error(e)
        }
    }
}

export const passkeyConditionalField = {
    ...formView,
    Renderer: PasskeyConditionalField,
};

registry.category("views").add("passkey_conditional_field", passkeyConditionalField);

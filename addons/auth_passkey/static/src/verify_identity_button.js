/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

import { Component } from "@odoo/owl";
import { startAuthentication } from "../lib/simplewebauthn.js"

export class VerifyIdentityPasskey extends Component {
    setup() {
        this.actionService = useService("action")
        this.rpc = useService("rpc")
        this.title = _t('Use Passkey')
    }

    async identityVerificationPasskey() {
        try {
            const serverOptions = await this.rpc("/auth/passkey/start-auth")
            const auth = await startAuthentication(serverOptions)
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

export const verifyIdentityPasskey = {
    component: VerifyIdentityPasskey,
}

VerifyIdentityPasskey.template = "auth_passkey.VerifyIdentityPasskeyButton";
registry.category('view_widgets').add('verify_identity_passkey', verifyIdentityPasskey);

/** @odoo-module **/

import { jsonrpc } from "@web/core/network/rpc_service"
import publicWidget from "@web/legacy/js/public/public_widget"
import { startAuthentication } from "../lib/simplewebauthn.js"

publicWidget.registry.passkeyLogin = publicWidget.Widget.extend({
    selector: '.passkey_login_link',
    events: { 'click': '_onclick' },

    _onclick: async function() {
        try {
            const serverOptions = await jsonrpc("/auth/passkey/start-auth")
            const auth = await startAuthentication(serverOptions)
            const verification = await jsonrpc("/auth/passkey/verify-auth", {auth: auth})
            if(verification.status == "ok") {
                window.location.href = verification.redirect_url
            }
        } catch(e) {
            console.error(e)
        }
    }
})

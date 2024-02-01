/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Many2OneField, many2OneField } from "@web/views/fields/many2one/many2one_field"

class PasskeyCard extends Many2OneField {
//    static template = "auth.passkeys.PasskeyCard"
}

registry.category("fields").add("auth_passkeys_card", {...many2OneField, component: PasskeyCard});

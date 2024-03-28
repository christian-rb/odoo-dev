/** @odoo-module */
import { AvatarCardPopover } from "@mail/discuss/web/avatar_card/avatar_card_popover";
/** @type {ReturnType<import("@mail/utils/common/misc").rpcWithEnv>} */
let rpc;
import { rpcWithEnv } from "@mail/utils/common/misc";

export class PartnerAvatarCardPopover extends AvatarCardPopover {
    setup() {
        super.setup();
        this.avatarModel = "res.partner";
        rpc = rpcWithEnv(this.env);
    }

    async getData() {
        return await rpc("/mail/partner_avatar_card/info", {
            avatar_id: this.props.id,
            userFieldNames: this.fieldNames,
        });
    }
}

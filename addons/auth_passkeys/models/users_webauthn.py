from odoo import fields, models

class UsersWebauthKeys(models.Model):
    _inherit = "res.users"

    auth_passkeys_key_ids = fields.One2many("auth.passkeys.key", "create_uid")

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ['auth_passkeys_key_ids']

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ['auth_passkeys_key_ids']

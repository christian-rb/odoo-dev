import base64

from odoo import api, fields, models, _
from odoo.addons.base.models.res_users import check_identity


class PassKey(models.Model):
    _name = "auth.passkey.key"
    _description = "Passkeys"
    _order = "id desc"

    name = fields.Char(required=True)
    credential_identifier = fields.Char(required=True, groups='base.group_system')
    public_key = fields.Char(required=True, groups='base.group_system')
    sign_count = fields.Integer(default=0, groups='base.group_system')

    _sql_constraints = [
        ('unique_identifier', 'UNIQUE(credential_identifier)', 'The credential identifier should be unique.'),
    ]

    def _get_user_by_credential_id(self, identifier):
        identifier = base64.urlsafe_b64decode(identifier).hex()
        result = self.sudo().search([("credential_identifier", "=", identifier)])
        return result

    @check_identity
    @api.model
    def action_new_passkey(self, key):
        self.env.cr.execute("""
        INSERT INTO {table} (name, credential_identifier, public_key, create_uid)
        VALUES (%s, %s, %s, %s)
        """.format(table=self._table), [
            key['name'],
            base64.urlsafe_b64decode(key['credential_identifier']).hex(),
            key['public_key'],
            self.env.user.id,
        ])

    @check_identity
    def action_delete_passkey(self):
        for key in self:
            if key.create_uid.id == self.env.user.id:
                key.sudo().unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Successfully deleted Passkey'),
                'type': 'success',
                'next': {
                    'type': 'ir.actions.client',
                    'tag': 'soft_reload',
                },
            }
        }

    def action_rename_passkey(self):
        return {
            'name': _('Rename Passkey'),
            'type': 'ir.actions.act_window',
            'res_model': 'auth.passkey.key',
            'view_id': self.env.ref('auth_passkey.auth_passkey_key_rename').id,
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
            'context': {
                'dialog_size': 'medium',
            }
        }

# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    chat_room_server_domain = fields.Char(
        'Default Discuss Server Domain',
        default='localhost:8069',  # TODO: find a way to get the actual url of the server
        config_parameter='website_discuss_room.chat_room_server_domain',
        help='The Odoo Discuss server domain can be customized through the settings to use a different server than the default "localhost:8069"')

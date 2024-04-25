# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class ChatRoom(models.Model):
    _inherit = "chat.room"

    def _compute_chat_room_server_domain(self):
        jitsi_server_domain = self.env['ir.config_parameter'].sudo().get_param(
            'website_jitsi.jitsi_server_domain', 'meet.jit.si')

        for room in self:
            room.jitsi_server_domain = jitsi_server_domain

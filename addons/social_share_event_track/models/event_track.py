from odoo import models


class EventTrack(models.Model):
    _inherit = 'event.track'

    def _snshare_allowed_model(self):
        return True

    def _snshare_allowed_fields(self):
        return ['event_id', 'image', 'name', 'partner_id']

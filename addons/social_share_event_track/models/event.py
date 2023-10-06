from odoo import models


class Event(models.Model):
    _inherit = 'event.event'

    def _snshare_allowed_fields(self):
        return ['name']

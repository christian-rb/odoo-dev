from odoo import models


class Partner(models.Model):
    _inherit = 'res.partner'

    def _snshare_allowed_model(self):
        return True

    def _snshare_allowed_fields(self):
        return ['name', 'phone', 'mobile', 'email', 'country_id']

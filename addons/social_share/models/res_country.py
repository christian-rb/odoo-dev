from odoo import models

class Country(models.Model):
    _inherit = 'res.country'

    def _snshare_allowed_fields(self):
        return ['name']

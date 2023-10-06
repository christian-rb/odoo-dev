
from odoo import fields, models

class Campaign(models.Model):
    _inherit = 'snshare.campaign'

    model = fields.Selection(string="Model Name", selection_add=[('event.track', 'Event Track')])

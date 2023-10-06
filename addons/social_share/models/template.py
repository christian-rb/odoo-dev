from odoo import fields, models

TEMPLATE_DIMENSIONS = (1200, 630)
TEMPLATE_RATIO = 40 / 21

class CampaignTemplate(models.Model):
    _inherit = 'mail.render.mixin'
    _name = 'snshare.template'
    _description = 'Social Share Template'

    name = fields.Char(required=True)
    template_group_id = fields.Many2one('snshare.template.group', ondelete="cascade")
    body = fields.Html(sanitize=False, translate=True)

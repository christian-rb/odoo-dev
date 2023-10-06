from odoo import fields, models

class CampaignTemplate(models.Model):
    _inherit = 'mail.render.mixin'
    _name = 'snshare.template.group'
    _description = 'Indicative group of alike templates.'

    name = fields.Char(required=True)
    template_ids = fields.One2many('snshare.template', inverse_name='template_group_id')
    model_id = fields.Many2one('ir.model')

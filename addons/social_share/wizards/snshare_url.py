# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from ..controllers.main import SocialShareController
from ..utils.image_utils import scale_image_b64


class SocialShareUrlShare(models.TransientModel):
    _name = 'snshare.url.share'
    _description = 'Social Share URL Wizard'

    campaign_id = fields.Many2one('snshare.campaign')
    model_id = fields.Many2one('ir.model', related='campaign_id.model_id')
    res_id = fields.Reference(selection="_selection_res_id", string="Record")
    image = fields.Image(compute='_compute_image')  # TODO find a way to prevent front-end from sending this again in onchange
    url_id = fields.Many2one('snshare.url', compute='_compute_url_id', string="Url Resolver")
    url = fields.Char(compute='_compute_url', string="Link")

    def _selection_res_id(self):
        groups = self.env['snshare.campaign']._read_group(
            domain=[('model_id', '!=', False)],
            groupby=['model_id'],
        )
        return [(model.model, model.display_name) for model, *_ in groups]

    @api.depends('campaign_id', 'res_id')
    def _compute_image(self):
        self.image = False
        for share_wizard in self:
            image = None
            if share_wizard.res_id:
                image = share_wizard.campaign_id._get_images_b64(record=share_wizard.res_id)[0]
            elif not share_wizard.model_id:
                image = share_wizard.campaign_id._get_images_b64(record=None)[0]
            if image:
                share_wizard.image = scale_image_b64(image, 0.5)

    @api.depends('campaign_id', 'res_id')
    def _compute_url_id(self):
        for share_wizard in self:
            if not share_wizard.model_id or not share_wizard.res_id:
                share_wizard.url_id = False
                continue
            url_id = self.env['snshare.url'].sudo().search([
                ('campaign_id', '=', share_wizard.campaign_id.id),
                ('res_id', '=', share_wizard.res_id.id)
            ])
            if not url_id:
                url_id = self.env['snshare.url'].sudo().create({
                    'campaign_id': share_wizard.campaign_id.id,
                    'res_id': share_wizard.res_id.id
                })
            share_wizard.url_id = url_id

    @api.depends('url_id', 'campaign_id')
    def _compute_url(self):
        for share_wizard in self:
            uuid = share_wizard.url_id.uuid if share_wizard.model_id else ''
            share_wizard.url = SocialShareController._get_campaign_url(
                share_wizard.campaign_id, uuid
            )

    def action_apply_to_url(self):
        return {'type': 'ir.actions.act_window_close'}

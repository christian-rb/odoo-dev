# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import secrets
from datetime import datetime, timedelta

from odoo import api, fields, models


class SocialShareUrl(models.Model):
    _name = 'snshare.url'
    _description = 'Social Share URL resolver'

    campaign_id = fields.Many2one('snshare.campaign')
    model_id = fields.Many2one('ir.model', related='campaign_id.model_id')
    record_name = fields.Char(compute='_compute_record_name')
    res_id = fields.Many2oneReference('Record', model_field='model_id')
    visited = fields.Boolean('Share URL Visited')
    shared = fields.Boolean('Shared on Social Networks')
    uuid = fields.Char(
        'Unique Access Token', default=lambda self: secrets.token_urlsafe(),
        readonly=True, required=True
    )
    image = fields.Image()
    # TODO  maybe store the image here and have a cron clean up after x minutes to avoid spamming compute for no reason

    _sql_constraints = [
        ('campaign_record_unique', 'unique(campaign_id, res_id)',
         'Each record should be unique for a campaign'),
        ('campaign_uuid_unique', 'unique(campaign_id, uuid)',
         'Each uuid should be unique for a campaign'),
    ]

    @api.depends('model_id', 'res_id')
    def _compute_record_name(self):
        for url in self:
            url.record_name = self.env[url.model_id.model].browse(url.res_id).display_name

    @api.autovacuum
    def _gc_snshare_urls(self):
        """Remove cached image after a while."""
        self.search([('write_date', '<=', datetime.now() - timedelta(days=30))]).image = False

    def _get_image(self):
        # compute if not already stored
        if not self.image:
            self.image = self.campaign_id._get_images_b64(record=self.env[self.model_id.model].browse(self.res_id))[0]
        return self.image

    def _get_image_bytes(self):
        return base64.b64decode(self._get_image())

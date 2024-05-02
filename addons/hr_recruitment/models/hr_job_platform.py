# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models, api


class JobPlatform(models.Model):
    _name = "hr.job.platform"
    _description = 'Job Platforms'

    name = fields.Char(required=True)
    email = fields.Char(required=True)
    subject_regex = fields.Char()

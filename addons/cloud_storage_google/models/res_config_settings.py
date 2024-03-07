# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64

from odoo import models, fields, api


class CloudStorageSettings(models.TransientModel):
    """
    Instructions:
    cloud_storage_google_bucket_name: if changed and the old bucket name
        are still in use, you should promise the current service account
        has the permission to access the old bucket.
    """
    _inherit = 'res.config.settings'

    cloud_storage_provider = fields.Selection(selection_add=[('google', 'Google Cloud Storage')])

    cloud_storage_google_bucket_name = fields.Char(
        string='Google Bucket Name',
        config_parameter='cloud_storage_google_bucket_name')
    # Google Service Account Key in JSON format
    cloud_storage_google_service_account_key = fields.Binary(
        string='Google Service Account Key', store=False
    )
    cloud_storage_google_account_info = fields.Char(
        string='Google Service Account Info',
        compute='_compute_cloud_storage_google_account_info',
        store=True,
        readonly=False,
        config_parameter='cloud_storage_google_account_info',
    )

    def get_values(self):
        res = super().get_values()
        if account_info := self.env['ir.config_parameter'].sudo().get_param('cloud_storage_google_account_info'):
            res['cloud_storage_google_service_account_key'] = base64.b64encode(account_info.encode())
        return res

    @api.onchange('cloud_storage_google_service_account_key')
    def _compute_cloud_storage_google_account_info(self):
        for setting in self:
            setting.cloud_storage_google_account_info = base64.b64decode(setting.with_context(bin_size=False).cloud_storage_google_service_account_key or b'') or False

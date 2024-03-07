# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _
from odoo.exceptions import UserError

from odoo.addons.cloud_storage.models.ir_attachment import DEFAULT_CLOUD_STORAGE_MIN_FILE_SIZE


class CloudStorageSettings(models.TransientModel):
    """
    Instructions:
    cloud_storage_provider: Once set, new attachments from the web client can
        be created as cloud storage attachments. Once unset, new attachments
        from the web client cannot be uploaded as cloud storage attachments.
        but existing cloud storage attachments can still be downloaded/deleted.
    cloud_storage_mim_file_size: a soft limit for the file size that can be
        uploaded as the cloud storage attachments for web client.
    cloud_storage_manual_delete: if disabled, the cloud storage blob will be
        deleted when the attachment is deleted from the server. And the account
        provided should have the blob deletion permission. If enabled, the
        administrator needs to manually delete them with scripts.
    """
    _inherit = 'res.config.settings'

    cloud_storage_provider = fields.Selection(
        selection=[],
        string='Cloud Storage Provider for new attachments',
        config_parameter='cloud_storage_provider',
    )

    cloud_storage_provider_count = fields.Integer(
        default=lambda self: len(self._fields['cloud_storage_provider'].selection)
    )

    cloud_storage_min_file_size = fields.Integer(
        string='Minimum File Size (bytes)',
        help='''webclient can upload files larger than the minimum file size
        (in bytes) as url attachments to the server and then upload the file to
        the cloud storage.''',
        config_parameter='cloud_storage_min_file_size',
        default=DEFAULT_CLOUD_STORAGE_MIN_FILE_SIZE,
    )

    def set_values(self):
        cloud_storage_configuration_before = self.env['cloud.storage.provider']._get_configuration()
        super().set_values()
        cloud_storage_configuration = self.env['cloud.storage.provider']._get_configuration()
        if not cloud_storage_configuration and self.cloud_storage_provider:
            raise UserError(_('Please configure the Cloud Storage before enabling it'))
        if cloud_storage_configuration and cloud_storage_configuration != cloud_storage_configuration_before:
            self.env['cloud.storage.provider']._setup()

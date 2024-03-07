# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _
from odoo.exceptions import UserError


DEFAULT_CLOUD_STORAGE_MIN_FILE_SIZE = 20 * (10 ** 6)


class CloudStorageProvider(models.AbstractModel):
    """
    Abstract model for cloud storage providers.
    There should be one cloud storage provider installed to override the methods
    """
    _name = 'cloud.storage.provider'
    _description = 'Cloud Storage Provider'

    def _generate_blob_name(self, attachment):
        """
        Generate a unique blob name for the attachment
        :param attachment: an ir.attachment record
        :return: A unique blob name str
        """
        return f'{attachment.id}/{attachment.name}'

    # Implement the following methods for each cloud storage provider.
    def _setup(self):
        """
        Setup the cloud storage provider and check the validity of the account
        info after saving the config in settings.
        return: None
        """
        pass

    def _get_configuration(self):
        """
        Return the configuration for the cloud storage provider. If the cloud
        storage provider is not fully configured, return an empty dict.
        :return: A configuration dict
        """
        return {}

    def _generate_url(self, attachment):
        """
        Generate a cloud blob url without signature or token for the attachment.
        This url is only used to identify the cloud blob.
        :param attachment: an ir.attachment record
        :return: A cloud blob url str
        """
        raise NotImplementedError()

    def _generate_download_info(self, attachment):
        """
        Generate the download info for the public client to directly download
        the attachment's blob from the cloud storage.
        :param attachment: an ir.attachment record
        :return: An download_info dictionary containing:
            * download_url: cloud storage url with permission to download the file
            * time_to_expiry: the time in seconds before the download url expires
        """
        raise NotImplementedError()

    def _generate_upload_info(self, attachment):
        """
        Generate the upload info for the public client to directly upload a
        file to the cloud storage.
        :param attachment: an ir.attachment record
        :return: An upload_info dictionary containing:
            * upload_url: cloud storage url with permission to upload the file
            * method: the request method used to upload the file
            * response_status: the status of the response for a successful
                upload request
            * [Optionally] headers: a dictionary of headers to be added to the
                upload request
        """
        raise NotImplementedError()


class CloudStorageAttachment(models.Model):
    _inherit = 'ir.attachment'

    type = fields.Selection(
        selection_add=[('cloud_storage', 'Cloud Storage')],
        ondelete={'cloud_storage': lambda recs: recs.write({'type': 'url'})}
    )

    def _post_add_create(self, **kwargs):
        super()._post_add_create(**kwargs)
        if kwargs.get('cloud_storage'):
            if not self.env['ir.config_parameter'].sudo().get_param('cloud_storage_provider'):
                raise UserError(_('Cloud Storage is not enabled'))
            for record in self:
                record.write({
                    'raw': False,
                    'type': 'cloud_storage',
                    'url': self.env['cloud.storage.provider']._generate_url(record)
                })

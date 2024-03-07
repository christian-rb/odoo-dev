# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
import requests
from datetime import datetime, timedelta, date, timezone
from urllib.parse import unquote, quote

from odoo import models, _
from odoo.exceptions import ValidationError
from odoo.tools import ormcache

from ..utils.cloud_storage_azure_utils import generate_blob_sas, get_user_delegation_key


class CloudStorageAzure(models.AbstractModel):
    _inherit = 'cloud.storage.provider'
    _description = 'Azure Cloud Storage'

    _url_pattern = re.compile(r'https://(?P<account_name>[\w]+).blob.core.windows.net/(?P<container_name>[\w]+)/(?P<blob_name>[^?]+)')
    _upload_url_time_to_expiry = 300  # 300 seconds
    _download_url_time_to_expiry = 300  # 300 seconds

    def _get_info_from_url(self, url):
        match = self._url_pattern.match(url)
        if not match:
            raise ValidationError(_('%s is not a valid Azure Blob Storage URL.'), url)
        return {
            'account_name': match['account_name'],
            'container_name': match['container_name'],
            'blob_name': unquote(match['blob_name']),
        }

    def _get_user_delegation_key(self):
        """ re-generate user_delegation_key every Monday and Friday which won't expire before regeneration """
        today = date.today()
        return self._generate_user_delegation_key(key_id=today - timedelta(days=today.weekday() % 4), days=7)

    @ormcache('key_id')
    def _generate_user_delegation_key(self, key_id, days=7):
        key_start_time = datetime.now(timezone.utc)
        key_expiry_time = key_start_time + timedelta(days=days)
        return get_user_delegation_key(
            tenant_id=self.env['ir.config_parameter'].sudo().get_param('cloud_storage_azure_tenant_id'),
            client_id=self.env['ir.config_parameter'].sudo().get_param('cloud_storage_azure_client_id'),
            client_secret=self.env['ir.config_parameter'].sudo().get_param('cloud_storage_azure_client_secret'),
            account_name=self.env['ir.config_parameter'].sudo().get_param('cloud_storage_azure_account_name'),
            key_start_time=key_start_time,
            key_expiry_time=key_expiry_time,
        )

    def _generate_sas_url(self, **kwargs):
        token = generate_blob_sas(user_delegation_key=self._get_user_delegation_key(), **kwargs)
        return f"https://{kwargs['account_name']}.blob.core.windows.net/{kwargs['container_name']}/{quote(kwargs['blob_name'])}?{token}"

    # OVERRIDES
    def _setup(self):
        blob_info = {
            'account_name': self.env['ir.config_parameter'].sudo().get_param('cloud_storage_azure_account_name'),
            'container_name': self.env['ir.config_parameter'].sudo().get_param('cloud_storage_azure_container_name'),
            # use different blob names in case the credentials are allowed to
            # overwrite an existing blob created by previous tests
            'blob_name': f'0/{datetime.now(timezone.utc)}.txt',
        }

        # check blob create permission
        upload_expiry = datetime.now(timezone.utc) + timedelta(seconds=self._upload_url_time_to_expiry)
        upload_url = self._generate_sas_url(**blob_info, permission='c', expiry=upload_expiry)
        upload_response = requests.put(upload_url, data=b'', headers={'x-ms-blob-type': 'BlockBlob'}, timeout=5)
        if upload_response.status_code != 201:
            raise ValidationError(_('The connection string is not allowed to upload blobs to the container.\n%s', str(upload_response.text)))

        # check blob read permission
        download_expiry = datetime.now(timezone.utc) + timedelta(seconds=self._download_url_time_to_expiry)
        download_url = self._generate_sas_url(**blob_info, permission='r', expiry=download_expiry)
        download_response = requests.get(download_url, timeout=5)
        if download_response.status_code != 200:
            raise ValidationError(_('The connection string is not allowed to download blobs from the container.\n%s', str(download_response.text)))

    def _get_configuration(self):
        configuration = {
            'container_name': self.env['ir.config_parameter'].get_param('cloud_storage_azure_container_name'),
            'account_name': self.env['ir.config_parameter'].get_param('cloud_storage_azure_account_name'),
            'tenant_id': self.env['ir.config_parameter'].get_param('cloud_storage_azure_tenant_id'),
            'client_id': self.env['ir.config_parameter'].get_param('cloud_storage_azure_client_id'),
            'client_secret': self.env['ir.config_parameter'].get_param('cloud_storage_azure_client_secret'),
        }
        return configuration if all(configuration.values()) else {}

    def _generate_url(self, attachment):
        account_name = self.env['ir.config_parameter'].sudo().get_param('cloud_storage_azure_account_name')
        container_name = self.env['ir.config_parameter'].sudo().get_param('cloud_storage_azure_container_name')
        blob_name = self._generate_blob_name(attachment)
        return f"https://{account_name}.blob.core.windows.net/{container_name}/{quote(blob_name)}"

    def _generate_download_info(self, attachment):
        info = self._get_info_from_url(attachment.url)
        expiry = datetime.now(timezone.utc) + timedelta(seconds=self._download_url_time_to_expiry)
        return {
            'url': self._generate_sas_url(**info, permission='r', expiry=expiry, cache_control=f'private, max-age={self._download_url_time_to_expiry}'),
            'time_to_expiry': self._download_url_time_to_expiry,
        }

    def _generate_upload_info(self, attachment):
        info = self._get_info_from_url(attachment.url)
        expiry = datetime.now(timezone.utc) + timedelta(seconds=self._upload_url_time_to_expiry)
        url = self._generate_sas_url(**info, permission='c', expiry=expiry)
        return {
            'url': url,
            'method': 'PUT',
            'headers': {
                'x-ms-blob-type': 'BlockBlob',
            },
            'response_status': 201,
        }

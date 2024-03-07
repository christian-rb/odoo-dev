# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import re
import requests
from datetime import datetime, timezone
from urllib.parse import unquote, quote

try:
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request
except ImportError:
    service_account = Request = None

from odoo import models, _
from odoo.exceptions import ValidationError
from odoo.tools import ormcache

from ..utils.cloud_storage_google_utils import generate_signed_url_v4

GOOGLE_CLOUD_STORAGE_ENDPOINT = 'https://storage.googleapis.com'


class CloudStorageGoogle(models.AbstractModel):
    _inherit = 'cloud.storage.provider'
    _description = 'Google Cloud Storage'

    _url_pattern = re.compile(rf'{GOOGLE_CLOUD_STORAGE_ENDPOINT}/(?P<bucket_name>[\w\-.]+)/(?P<blob_name>[^?]+)')
    _upload_url_time_to_expiry = 300  # 300 seconds
    _download_url_time_to_expiry = 300  # 300 seconds

    def _get_info_from_url(self, url):
        match = self._url_pattern.match(url)
        if not match:
            raise ValidationError(_('%s is not a valid Google Cloud Storage URL.'), url)
        return {
            'bucket_name': match['bucket_name'],
            'blob_name': unquote(match['blob_name']),
        }

    def _generate_signed_url(self, bucket_name, blob_name, **kwargs):
        quote_blob_name = quote(blob_name)
        resource = f'/{bucket_name}/{quote_blob_name}'
        return generate_signed_url_v4(
            credentials=self._get_credentials(),
            resource=resource,
            api_access_endpoint=GOOGLE_CLOUD_STORAGE_ENDPOINT,
            **kwargs,
        )

    @ormcache()
    def _get_credentials(self):
        """ Get the credentials object of currently used account info.
        This method is cached to because from_service_account_info is slow.
        """
        account_info = json.loads(self.env['ir.config_parameter'].sudo().get_param('cloud_storage_google_account_info'))
        credentials = service_account.Credentials.from_service_account_info(account_info)
        return credentials

    # OVERRIDES
    def _setup(self):
        # check bucket access
        bucket_name = self.env['ir.config_parameter'].sudo().get_param('cloud_storage_google_bucket_name')
        # use different blob names in case the credentials are allowed to
        # overwrite an existing blob created by previous tests
        blob_name = f'0/{datetime.now(timezone.utc)}.txt'

        # check blob create permission
        upload_url = self._generate_signed_url(bucket_name, blob_name, method='PUT', expiration=self._upload_url_time_to_expiry)
        upload_response = requests.put(upload_url, data=b'', timeout=5)
        if upload_response.status_code != 200:
            raise ValidationError(_('The account info is not allowed to upload blobs to the bucket.\n%s', str(upload_response.text)))

        # check blob read permission
        download_url = self._generate_signed_url(bucket_name, blob_name, method='GET', expiration=self._download_url_time_to_expiry)
        download_response = requests.get(download_url, timeout=5)
        if download_response.status_code != 200:
            raise ValidationError(_('The account info is not allowed to download blobs from the bucket.\n%s', str(upload_response.text)))

        # CORS management is not allowed in the Google Cloud console.
        # configure CORS on bucket to allow .pdf preview and direct upload
        cors = [{
            'origin': ['*'],
            'method': ['GET', 'PUT'],
            'responseHeader': ['Content-Type'],
            'maxAgeSeconds': self._download_url_time_to_expiry,
        }]
        credentials = self._get_credentials().with_scopes(['https://www.googleapis.com/auth/devstorage.full_control'])
        credentials.refresh(Request())
        url = f"{GOOGLE_CLOUD_STORAGE_ENDPOINT}/storage/v1/b/{bucket_name}?fields=cors"
        headers = {
            'Authorization': f'Bearer {credentials.token}',
            'Content-Type': 'application/json'
        }
        data = json.dumps({'cors': cors})
        patch_response = requests.patch(url, data=data, headers=headers, timeout=5)
        if patch_response.status_code != 200:
            raise ValidationError(_("The account info is not allowed to set the bucket's CORS.\n%s", str(patch_response.text)))

    def _get_configuration(self):
        configuration = {
            'bucket_name': self.env['ir.config_parameter'].get_param('cloud_storage_google_bucket_name'),
            'account_info': self.env['ir.config_parameter'].get_param('cloud_storage_google_account_info'),
        }
        return configuration if all(configuration.values()) else {}

    def _generate_url(self, attachment):
        blob_name = self._generate_blob_name(attachment)
        bucket_name = self.env['ir.config_parameter'].sudo().get_param('cloud_storage_google_bucket_name')
        return f"{GOOGLE_CLOUD_STORAGE_ENDPOINT}/{bucket_name}/{quote(blob_name)}"

    def _generate_download_info(self, attachment):
        info = self._get_info_from_url(attachment.url)
        return {
            'url': self._generate_signed_url(info['bucket_name'], info['blob_name'], method='GET', expiration=self._download_url_time_to_expiry),
            'time_to_expiry': self._download_url_time_to_expiry,
        }

    def _generate_upload_info(self, attachment):
        info = self._get_info_from_url(attachment.url)
        return {
            'url': self._generate_signed_url(info['bucket_name'], info['blob_name'], method='PUT', expiration=self._upload_url_time_to_expiry),
            'method': 'PUT',
            'response_status': 200,
        }

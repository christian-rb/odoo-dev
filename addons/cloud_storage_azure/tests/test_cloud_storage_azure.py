# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import requests

from requests import Response
from unittest.mock import patch

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError

from ..utils.cloud_storage_azure_utils import UserDelegationKey
from .. import uninstall_hook


class TestCloudStorageAzure(TransactionCase):

    def setUp(self):
        super().setUp()
        self.DUMMY_AZURE_ACCOUNT_NAME = 'accountname'
        self.DUMMY_AZURE_TENANT_ID = 'tenantid'
        self.DUMMY_AZURE_CLIENT_ID = 'clientid'
        self.DUMMY_AZURE_CLIENT_SECRET = 'secret'
        self.container_name = 'container_name'
        self.env['ir.config_parameter'].set_param('cloud_storage_provider', 'azure')
        self.env['ir.config_parameter'].set_param('cloud_storage_azure_account_name', self.DUMMY_AZURE_ACCOUNT_NAME)
        self.env['ir.config_parameter'].set_param('cloud_storage_azure_tenant_id', self.DUMMY_AZURE_TENANT_ID)
        self.env['ir.config_parameter'].set_param('cloud_storage_azure_client_id', self.DUMMY_AZURE_CLIENT_ID)
        self.env['ir.config_parameter'].set_param('cloud_storage_azure_client_secret', self.DUMMY_AZURE_CLIENT_SECRET)
        self.env['ir.config_parameter'].set_param('cloud_storage_azure_container_name', self.container_name)

        self.DUMMY_USER_DELEGATION_KEY = UserDelegationKey()
        self.DUMMY_USER_DELEGATION_KEY.signed_oid = 'signed_oid'
        self.DUMMY_USER_DELEGATION_KEY.signed_tid = 'signed_tid'
        self.DUMMY_USER_DELEGATION_KEY.signed_start = '2024-04-12T08:57:35Z'
        self.DUMMY_USER_DELEGATION_KEY.signed_expiry = '2024-04-13T09:57:35Z'
        self.DUMMY_USER_DELEGATION_KEY.signed_service = 'b'
        self.DUMMY_USER_DELEGATION_KEY.signed_version = '2023-11-03'
        self.DUMMY_USER_DELEGATION_KEY.value = 'KEHG9q+1y6XGLHkDNv3pR2DhmbOfxeTf5KAJ5/ssNpU='

        self.DUMMY_USER_DELEGATION_KEY_XML = bytes(f"""<?xml version="1.0" encoding="utf-8"?>
        <UserDelegationKey>
            <SignedOid>{self.DUMMY_USER_DELEGATION_KEY.signed_oid}</SignedOid>
            <SignedTid>{self.DUMMY_USER_DELEGATION_KEY.signed_tid}</SignedTid>
            <SignedStart>{self.DUMMY_USER_DELEGATION_KEY.signed_start}</SignedStart>
            <SignedExpiry>{self.DUMMY_USER_DELEGATION_KEY.signed_expiry}</SignedExpiry>
            <SignedService>{self.DUMMY_USER_DELEGATION_KEY.signed_service}</SignedService>
            <SignedVersion>{self.DUMMY_USER_DELEGATION_KEY.signed_version}</SignedVersion>
            <Value>{self.DUMMY_USER_DELEGATION_KEY.value}</Value>
        </UserDelegationKey>""", 'utf-8')

    def test_generate_user_delegation_key_success(self):
        def post(url, **kwargs):
            response = Response()
            if url.startswith('https://login.microsoftonline.com'):
                response.status_code = 200
                response._content = bytes(json.dumps({'access_token': 'xxx'}), 'utf-8')
            if 'blob.core.windows.net' in url:
                response.status_code = 200
                response._content = self.DUMMY_USER_DELEGATION_KEY_XML
            return response

        with patch('odoo.addons.cloud_storage_azure.utils.cloud_storage_azure_utils.requests.post', post):
            self.env['cloud.storage.provider']._generate_user_delegation_key(key_id=1)

    def test_generate_user_delegation_key_wrong_info(self):
        def post(url, **kwargs):
            response = Response()
            if url.startswith('https://login.microsoftonline.com'):
                response.status_code = 400  # bad request because of missing tenant_id and client_id are wrong
            if 'blob.core.windows.net' in url:
                response.status_code = 200
                response._content = self.DUMMY_USER_DELEGATION_KEY_XML
            return response

        with patch('odoo.addons.cloud_storage_azure.utils.cloud_storage_azure_utils.requests.post', post):
            with self.assertRaises(ValidationError):
                self.env['cloud.storage.provider']._generate_user_delegation_key(key_id=1)

    def test_generate_user_delegation_key_wrong_secret(self):
        def post(url, **kwargs):
            response = Response()
            if url.startswith('https://login.microsoftonline.com'):
                response.status_code = 401  # forbidden because the secret is wrong
            if 'blob.core.windows.net' in url:
                response.status_code = 200
                response._content = self.DUMMY_USER_DELEGATION_KEY_XML
            return response

        with patch('odoo.addons.cloud_storage_azure.utils.cloud_storage_azure_utils.requests.post', post):
            with self.assertRaises(ValidationError):
                self.env['cloud.storage.provider']._generate_user_delegation_key(key_id=1)

    def test_generate_user_delegation_key_wrong_account(self):
        def post(url, **kwargs):
            response = Response()
            if url.startswith('https://login.microsoftonline.com'):
                response.status_code = 200
                response._content = bytes(json.dumps({'access_token': 'xxx'}), 'utf-8')
            if 'blob.core.windows.net' in url:
                raise requests.exceptions.ConnectionError()  # account_name wrong: domain https://accountname.blob.core.windows.net doesn't exist
            return response

        with patch('odoo.addons.cloud_storage_azure.utils.cloud_storage_azure_utils.requests.post', post), \
             self.assertRaises(ValidationError):
            self.env['cloud.storage.provider']._generate_user_delegation_key(key_id=1)

    def test_generate_sas_url(self):
        with patch('odoo.addons.cloud_storage_azure.models.cloud_storage_azure.CloudStorageAzure._generate_user_delegation_key', return_value=self.DUMMY_USER_DELEGATION_KEY):
            # create test cloud attachment like route "/mail/attachment/upload"
            # with dummy binary
            attachment = self.env['ir.attachment'].create([{
                'name': 'test.txt',
                'mimetype': 'text/plain',
                'datas': b'',
            }])
            attachment._post_add_create(cloud_storage=True)
            self.env['cloud.storage.provider']._generate_upload_info(attachment)
            self.env['cloud.storage.provider']._generate_download_info(attachment)

    def test_uninstall_fail(self):
        with self.assertRaises(UserError, msg="Don't uninstall the module if there are Azure attachments in use"):
            attachment = self.env['ir.attachment'].create([{
                'name': 'test.txt',
                'mimetype': 'text/plain',
                'datas': b'',
            }])
            attachment._post_add_create(cloud_storage=True)
            attachment.flush_recordset()
            uninstall_hook(self.env)

    def test_uninstall_success(self):
        uninstall_hook(self.env)
        # make sure all sensitive data are removed
        self.assertFalse(self.env['ir.config_parameter'].get_param('cloud_storage_provider'))
        self.assertFalse(self.env['ir.config_parameter'].get_param('cloud_storage_azure_account_name'))
        self.assertFalse(self.env['ir.config_parameter'].get_param('cloud_storage_azure_tenant_id'))
        self.assertFalse(self.env['ir.config_parameter'].get_param('cloud_storage_azure_client_id'))
        self.assertFalse(self.env['ir.config_parameter'].get_param('cloud_storage_azure_client_secret'))
        self.assertFalse(self.env['ir.config_parameter'].get_param('cloud_storage_azure_container_name'))

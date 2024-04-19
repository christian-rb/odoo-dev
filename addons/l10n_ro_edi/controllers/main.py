# Part of Odoo. See LICENSE file for full copyright and licensing details.

import requests
import base64

from datetime import datetime, timedelta
from odoo import _, http
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools import json
from werkzeug.urls import url_join, url_encode


ENDPOINT_AUTHORIZE = 'https://logincert.anaf.ro/anaf-oauth2/v1/authorize'
ENDPOINT_TOKEN = 'https://logincert.anaf.ro/anaf-oauth2/v1/token'
ENDPOINT_REVOKE = 'https://logincert.anaf.ro/anaf-oauth2/v1/revoke'


class EFacturaOAuthController(http.Controller):

    @http.route('/l10n_ro_edi/authorize/<int:company_id>')
    def authorize(self, company_id, **kw):
        """ Generate Authorization Token to acquire access_key for requesting Access Token """
        company = http.request.env['res.company'].sudo().browse(company_id)
        if not company.l10n_ro_edi_client_id or not company.l10n_ro_edi_client_secret:
            raise UserError(_("Client ID and Client Secret field must be filled."))

        auth_url = url_join(ENDPOINT_AUTHORIZE, '?' + url_encode({
            'response_type': 'code',
            'client_id': company.l10n_ro_edi_client_id,
            'redirect_uri': company.l10n_ro_edi_callback_url,
            'token_content_type': 'jwt',
        }))
        return request.redirect(auth_url, code=302, local=False)

    @http.route('/l10n_ro_edi/callback/<int:company_id>', type='http', auth="user")
    def callback(self, company_id, **kw):
        """ Use the acquired access_key to request access & refresh token from ANAF """
        company = http.request.env['res.company'].sudo().browse(company_id)
        access_key = kw.get('code')
        # Without certificate, ANAF won't give any access key in the callback's "code" parameter
        if not access_key:
            error_message = _("Access key not found. Please try again.\nResponse: %s", kw)
            company.l10n_ro_edi_oauth_error = error_message
            company.env.cr.commit()
            raise UserError(error_message)

        response = requests.post(
            url='https://logincert.anaf.ro/anaf-oauth2/v1/token',
            data={
                "grant_type": "authorization_code",
                "client_id": company.l10n_ro_edi_client_id,
                "client_secret": company.l10n_ro_edi_client_secret,
                "code": access_key,
                "access_key": access_key,
                "redirect_uri": company.l10n_ro_edi_callback_url,
                "token_content_type": "jwt",
            },
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "accept": "application/json",
                "user-agent": "PostmanRuntime/7.29.2",
            },
            timeout=5,
        )
        response_json = response.json()
        if 'access_token' not in response_json or 'refresh_token' not in response_json:
            error_message = _("Token not found.\nResponse: %s", response_json)
            company.l10n_ro_edi_oauth_error = error_message
            company.env.cr.commit()
            raise UserError(error_message)

        # The access_token is in JWT format, which consists of 3 parts separated by '.':
        # Header, Payload, and Signature. We only need the Payload part to decode the token.
        # We also need to make sure to correctly pad the payload string to be decoded successfully.
        payload = response_json['access_token'].split('.')[1]
        payload += '=' * (-len(payload) % 4)
        decoded_payload = base64.urlsafe_b64decode(payload).decode('utf-8')
        access_token_obj = json.loads(decoded_payload)
        company.write({
            'l10n_ro_edi_access_token': access_token_obj['jti'],
            'l10n_ro_edi_refresh_token': response_json['refresh_token'],
            'l10n_ro_edi_access_expiry_date': datetime.fromtimestamp(access_token_obj['exp']),
            'l10n_ro_edi_refresh_expiry_date': datetime.now() + timedelta(days=364),
            'l10n_ro_edi_oauth_error': False,
        })
        return request.redirect(company.get_base_url())

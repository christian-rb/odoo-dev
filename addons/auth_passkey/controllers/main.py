import json
from base64 import urlsafe_b64encode
from werkzeug.urls import url_parse

from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError
from odoo.addons.web.controllers.utils import fix_view_modes
from odoo.addons.web.controllers.utils import _get_login_redirect_url
from ..lib.duo_labs.webauthn import base64url_to_bytes, generate_authentication_options, verify_authentication_response, generate_registration_options, verify_registration_response, options_to_json
from ..lib.duo_labs.webauthn.helpers.structs import AuthenticatorSelectionCriteria, ResidentKeyRequirement, UserVerificationRequirement


class WebauthnController(http.Controller):
    @http.route(['/auth/passkey/start-registration'], type='json', auth='public')
    def json_start_registration(self):
        base_url = request.env['auth.passkey.key'].get_base_url()
        parsed_url = url_parse(base_url)
        registration_options = generate_registration_options(
            rp_id=parsed_url.host,
            rp_name='Odoo',
            user_id=str(request.session.uid).encode(),
            user_name=request.session.login,
            authenticator_selection=AuthenticatorSelectionCriteria(
                resident_key=ResidentKeyRequirement.REQUIRED,
                user_verification=UserVerificationRequirement.REQUIRED
            )
        )
        request.session.webauthn_challenge = registration_options.challenge
        return json.loads(options_to_json(registration_options))

    @http.route(['/auth/passkey/verify-registration'], type='json', auth='public')
    def json_verify_registration(self, registration):
        base_url = request.env['auth.passkey.key'].get_base_url()
        parsed_url = url_parse(base_url)
        verification = verify_registration_response(
            credential=registration,
            expected_challenge=request.session.webauthn_challenge,
            expected_origin=parsed_url.replace(path='').to_url(),
            expected_rp_id=parsed_url.host,
        )
        return {'credentialId': urlsafe_b64encode(verification.credential_id),
                'credentialPublicKey': urlsafe_b64encode(verification.credential_public_key)}

    @http.route(['/auth/passkey/start-auth'], type='json', auth='public')
    def json_start_authentication(self):
        base_url = request.env['auth.passkey.key'].get_base_url()
        parsed_url = url_parse(base_url)
        auth_options = generate_authentication_options(
            rp_id=parsed_url.host,
            user_verification=UserVerificationRequirement.REQUIRED,
        )
        request.session.webauthn_challenge = auth_options.challenge
        return json.loads(options_to_json(auth_options))

    @http.route(['/auth/passkey/verify-auth'], type='json', auth='public')
    def json_verify_authentication(self, auth):
        base_url = request.env['auth.passkey.key'].get_base_url()
        parsed_url = url_parse(base_url)
        response = {'status': 'fail'}
        auth_key = request.env['auth.passkey.key']._get_user_by_credential_id(auth['id'])
        if auth_key:
            auth_verification = verify_authentication_response(
                credential=auth,
                expected_challenge=request.session.webauthn_challenge,
                expected_origin=parsed_url.replace(path='').to_url(),
                expected_rp_id=parsed_url.host,
                credential_public_key=base64url_to_bytes(auth_key.public_key),
                credential_current_sign_count=auth_key.sudo().sign_count,
            )
            auth_key.sudo().sign_count = auth_verification.new_sign_count

            verify_identity_id = auth.get('verify_identity_id')
            if verify_identity_id:
                idcheck = request.env['res.users.identitycheck'].browse(verify_identity_id)
                if len(idcheck) == 1 and idcheck.create_uid.id == request.env.user.id:
                    if request.env.user.id == auth_key.create_uid.id:
                        action = idcheck._bypass()
                        if action:
                            if 'view_mode' in action:
                                action = fix_view_modes(action)
                            response['status'] = 'ok'
                            response['action'] = action
                            return response
                    else:
                        raise ValidationError(_('This Passkey is not associated with this user.'))

            request.session.pre_login = auth_key.create_uid.login
            request.session.pre_uid = auth_key.create_uid.id
            request.session.finalize(request.env)
            response['status'] = 'ok'
            response['redirect_url'] = _get_login_redirect_url(auth_key.create_uid.id)
        return response

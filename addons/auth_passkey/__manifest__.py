{
    'name': 'Passkeys',
    'version': '1.0',
    'summary': 'Passkeys',
    'description': "The implementation of 2FA through passkeys using the webauthn protocol.",
    'category': 'Hidden/Tools',
    'depends': ['base_setup', 'web'],
    'external_dependencies': {
        'python': ['cbor2'],
    },
    'data': [
        'views/auth_passkey_key_views.xml',
        'views/auth_passkey_wizard_views.xml',
        'views/auth_signup_login_templates.xml',
        'views/res_users_views.xml',
        'views/res_users_identitycheck_views.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'auth_passkey/static/lib/simplewebauthn.js',
            'auth_passkey/static/src/create_passkey_button.js',
            'auth_passkey/static/src/create_passkey_button.xml',
            'auth_passkey/static/src/verify_identity_button.js',
            'auth_passkey/static/src/verify_identity_button.xml',
            'auth_passkey/static/src/conditional_access.js',
        ],
        'web.assets_frontend': [
            'auth_passkey/static/lib/simplewebauthn.js',
            'auth_passkey/static/src/login_passkeys.js',
        ],
    },
    'license': 'LGPL-3',
    'application': True,
}

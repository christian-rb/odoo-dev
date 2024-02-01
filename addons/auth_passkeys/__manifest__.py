{
    'name': 'Passkeys',
    'version': '1.0',
    'summary': 'Passkeys',
    'description': "The implementation of 2FA through passkeys using the webauthn protocol.",
    'category': 'Hidden/Tools',
    'depends': ['base_setup'],
    'data': [
        'views/res_users_views.xml',
        'views/auth_passkeys_key_views.xml',
        'views/auth_signup_login_templates.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'auth_passkeys/static/**/*',
        ],
        'web.assets_frontend_minimal': [
            'auth_passkeys/static/lib/simplewebauthn.js',
            'auth_passkeys/static/src/login_passkeys.js',
        ],
    },
    'license': 'OEEL-1',
}

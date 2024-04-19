# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'author': 'Odoo',
    'name': 'Romania - E-invoicing',
    'version': '1.0',
    'category': 'Accounting/Localizations/EDI',
    'description': """
E-invoice implementation for Romania
    """,
    'summary': "E-Invoice implementation for Romania",
    'countries': ['ro'],
    'depends': [
        'account_edi_ubl_cii',
        'l10n_ro',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
        'views/ciusro_document_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/account_move_send_views.xml',
    ],
    'installable': True,
    'auto_install': True,
    'license': 'LGPL-3',
}

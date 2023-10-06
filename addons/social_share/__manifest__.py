{
    'name': 'Social Share',
    'version': '1.0',
    'category': 'Marketing/Social Marketing',
    'summary': 'Generate dynamic shareable cards',
    'depends': ['link_tracker'],
    'data': [
        'security/social_share_security.xml',
        'security/ir.model.access.csv',
        'data/snshare_template_data.xml',
        'views/snshare_campaign_views.xml',
        'views/snshare_campaign_element_views.xml',
        'views/snshare_template_views.xml',
        'views/snshare_frontend.xml',
        'views/snshare_menus.xml',
        'views/snshare_url_views.xml',
        'wizards/snshare_url_views.xml',
        'wizards/snshare_url_multi_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'social_share/static/src/scss/*'
        ],
        'snshare.assets_share_campaign': [
            'social_share/static/src/share_campaign/**/*',
        ],
    },
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    "name": "Website Discuss Room",
    'category': 'Hidden',
    'version': '1.0',
    "summary": "Create Discuss room on website.",
    'website': 'https://www.odoo.com/app/events',
    "description": "Create Discuss room on website.",
    "depends": [
        "website"
    ],
    "data": [
        'views/chat_room_templates.xml',
        'views/chat_room_views.xml',
        'views/res_config_settings_views.xml',
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_discuss_room/static/src/css/chat_room.css',
            'website_discuss_room/static/src/js/chat_room.js',
            'website_discuss_room/static/src/xml/chat_room_modal.xml',
        ],
    },
    'license': 'LGPL-3',
}

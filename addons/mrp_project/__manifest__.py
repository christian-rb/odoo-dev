# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "MRP Project direct link",
    'version': '1.0',
    'summary': "Link MRP to Project",
    'category': 'Manufacturing/Manufacturing',
    'depends': ['mrp', 'project'],
    'data': [
        'views/project_project_views.xml',
        'views/mrp_production_views.xml',
    ],
    'auto_install': True,
    'license': 'LGPL-3',
}

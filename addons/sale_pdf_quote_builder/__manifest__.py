# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Sales PDF Quotation Builder",
    'category': 'Sales/Sales',
    'description': "Build nice quotations",
    'depends': ['sale_management'],
    'data': [
        'report/ir_actions_report.xml',

        'security/ir.model.access.csv',

        'views/pdf_quote_builder_form_field_whitelist.xml',
        'views/product_document_views.xml',
        'views/sale_order_template_views.xml',

        'wizards/res_config_settings_views.xml',
        'wizards/sale_pdf_quote_builder_whitelisting_wizard_views.xml',
    ],
    'demo': [
        'data/sale_pdf_quote_builder_demo.xml',
    ],
    'auto_install': True,
    'license': 'LGPL-3',
}

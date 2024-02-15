# Part of Odoo. See LICENSE file for full copyright and licensing details.

import requests
from datetime import timedelta
from lxml import etree

from odoo import models, fields, Command, _
from odoo.exceptions import UserError

ACCEPTED_ENDPOINTS = (
    'sendinvoices',
    'sendexpensesclassification',
    'requestdocs',
)

NAMESPACES = {"ns": "http://www.aade.gr/myDATA/invoice/v1.0"}

DEFAULT_TEST_ID = 'odoodev'
DEFAULT_TEST_VAT = '047747270'
DEFAULT_TEST_KEY = '20ea658627fd8c7d90594fe4601d3327'


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_gr_aade_user_id = fields.Char('AADE User ID')
    l10n_gr_subscription_key = fields.Char('AADE Subscription Key')

    l10n_gr_edi_test_env = fields.Boolean('Activate Test Environment', default=False)
    l10n_gr_edi_test_id = fields.Char('AADE Test User ID', required=True, default=DEFAULT_TEST_ID)
    l10n_gr_edi_test_vat = fields.Char('AADE Test User VAT', required=True, default=DEFAULT_TEST_VAT)
    l10n_gr_edi_test_key = fields.Char('AADE Test Subscription Key', required=True, default=DEFAULT_TEST_KEY)

    def _l10n_gr_edi_get_mydata_url(self, endpoint):
        """ Gets URL to send request to MyDATA API """
        if endpoint not in ACCEPTED_ENDPOINTS:
            raise Exception('Invalid MyDATA endpoint')
        if self.l10n_gr_edi_test_env:
            return f"https://mydataapidev.aade.gr/{endpoint}"
        else:
            return f"https://mydatapi.aade.gr/myDATA/{endpoint}"

    def _l10n_gr_edi_get_headers_credentials(self):
        """ Returns required credentials for header of all requests to MyDATA.
        To activate test credentials, set l10n_gr_edi_test_env=True """
        if self.l10n_gr_edi_test_env:
            return {
                'aade-user-id': self.l10n_gr_edi_test_id,
                'ocp-apim-subscription-key': self.l10n_gr_edi_test_key,
            }

        if not self.l10n_gr_aade_user_id or not self.l10n_gr_subscription_key:
            # Will not happen as we've checked from mydata_prepare_constraints check, but just in case
            raise UserError(_('MyDATA credentials not found on company %s', self.name))

        return {
            'aade-user-id': self.l10n_gr_aade_user_id,
            'ocp-apim-subscription-key': self.l10n_gr_subscription_key,
        }

    def cron_mydata_fetch_invoices(self):
        """ Receive issued MyDATA Invoices and create draft Vendor Bills based on the received XML. """
        gr_companies = self.env['res.company'].search([
            ('country_code', '=', 'GR'),
            '|', ('l10n_gr_edi_test_env', '=', True),  # uses test environment
            '&', ('l10n_gr_aade_user_id', '!=', False),  # uses real credential
                 ('l10n_gr_subscription_key', '!=', False)
        ])

        for gr_company in gr_companies:
            date_90_days_ago = (fields.Datetime.now() - timedelta(days=90)).strftime("%d/%m/%Y")
            date_today = fields.Datetime.now().strftime("%d/%m/%Y")

            response = requests.get(
                url=gr_company._l10n_gr_edi_get_mydata_url('requestdocs'),
                headers=gr_company._l10n_gr_edi_get_headers_credentials(),
                params={'mark': 0, 'dateFrom': date_90_days_ago, 'dateTo': date_today})

            root = etree.fromstring(response.content)
            pretty_xml = etree.tostring(root, encoding='unicode', pretty_print=True)
            print(pretty_xml)  # todo remove - monkey testing

            for invoice_element in root.xpath('//*[local-name()="invoice"]'):
                def find_value(element_name):
                    return invoice_element.findtext(f".//ns:{element_name}", namespaces=NAMESPACES)

                # Make sure to not create a duplicate bill
                if self.env['account.move'].search(
                        [('l10n_gr_edi_mark', '=', find_value('mark')), ('company_id', '=', gr_company.id)], limit=1):
                    continue

                # Get invoice lines data
                invoice_line_ids = []
                for detail_element in invoice_element.xpath('.//*[local-name()="invoiceDetails"]'):
                    tax_amount = {'1': 24.0, '2': 13.0, '3': 6.0, '4': 17.0, '5': 9.0, '6': 4.0, '7': 0.0, '8': 0.0}[
                        detail_element.findtext('.//ns:vatCategory', namespaces=NAMESPACES)]
                    invoice_line_ids.append(Command.create({
                        'price_unit': float(detail_element.findtext('.//ns:netValue', namespaces=NAMESPACES)),
                        'tax_ids': self.env['account.tax'].search([('amount', '=', tax_amount), ('company_id', '=', gr_company.id)], limit=1),
                    }))

                # Create draft Vendor Bill
                self.env['account.move'].sudo().create({
                    'state': 'draft',
                    'move_type': 'in_invoice',
                    'company_id': gr_company.id,
                    'partner_id': self.env['res.partner'].search([('vat', '=', find_value('vatNumber'))], limit=1),
                    'date': fields.Date.to_date(find_value('issueDate')),
                    'invoice_date': fields.Date.to_date(find_value('issueDate')),
                    'l10n_gr_edi_mark': find_value('mark'),
                    'l10n_gr_edi_inv_type': find_value('invoiceType'),
                    'invoice_line_ids': invoice_line_ids,
                })

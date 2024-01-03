# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import requests
import json

from json.decoder import JSONDecodeError
from markupsafe import Markup
from urllib.parse import urljoin

from odoo import api, fields, models, _
from odoo.addons.base.models.ir_qweb_fields import nl2br
from odoo.exceptions import ValidationError, UserError
from odoo.tools import file_open

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'
    # TODO - help strings for fields that appear in the company view
    l10n_ke_oscu_branch_code = fields.Char(
        related='partner_id.l10n_ke_oscu_branch_code',
        string='Branch ID',
        readonly=False, store=True,
    )
    l10n_ke_oscu_serial_number = fields.Char(string='Serial Number')
    l10n_ke_control_unit = fields.Char(
        string="Control Unit ID",
        help="This is retreived from the device during initialization."
    )
    l10n_ke_oscu_cmc_key = fields.Char(
        string='Device Communication Key',
        help="If you have an already initialized device, you can put your key here. ",
        groups="base.group_system")
    l10n_ke_oscu_is_active = fields.Boolean(
        string='Whether this company is set up for OSCU flows',
        compute='_compute_l10n_ke_oscu_is_active',
        search='_search_l10n_ke_oscu_is_active',
        compute_sudo=True,
    )

    l10n_ke_oscu_last_fetch_purchase_date = fields.Char(default='20180101000000')
    l10n_ke_oscu_last_fetch_customs_import_date = fields.Char(default='20180101000000')

    l10n_ke_insurance_code = fields.Char("Insurance Code")
    l10n_ke_insurance_name = fields.Char("Insurance Name")
    l10n_ke_insurance_rate = fields.Float("Insurance Rate")

    l10n_ke_server_mode = fields.Selection(
        selection=[
            ('prod', 'Production'),
            ('test', 'Test'),
            ('demo', 'Demo')
        ],
        string='eTIMS Server Mode',
        help="""
            - Production: Connection to eTIMS in production mode.
            - Test: Connection to eTIMS in test mode.
            - Demo: Mocked data, does not require an initialized OSCU.
        """,
    )

    # === Computes === #
    @api.depends('l10n_ke_oscu_cmc_key', 'l10n_ke_oscu_branch_code', 'l10n_ke_server_mode')
    def _compute_l10n_ke_oscu_is_active(self):
        for company in self:
            company.l10n_ke_oscu_is_active = (
                company.l10n_ke_server_mode == 'demo'
                or (
                    company.l10n_ke_server_mode in ['test', 'production']
                    and company.l10n_ke_oscu_cmc_key and company.l10n_ke_oscu_branch_code
                )
            )

    def _search_l10n_ke_oscu_is_active(self, operator, value):
        domain_true = [
            '|',
            ('l10n_ke_server_mode', '=', 'demo'),
            '&', '&',
            ('l10n_ke_server_mode', 'in', ['test', 'production']),
            ('l10n_ke_oscu_cmc_key', '!=', False),
            ('l10n_ke_oscu_branch_code', '!=', False),
        ]
        if (operator == '=' and value) or (operator == '!=' and not value):
            return domain_true
        elif (operator == '=' and not value) or (operator == '!=' and value):
            return ['!'] + domain_true

    def _l10n_ke_oscu_get_base_url(self):
        """ Returns the base url for the OSCU API depending on whether the company is in test mode """
        return f"https://etims-api{'-sbx' if self.l10n_ke_server_mode == 'test' else ''}.kra.go.ke/etims-api/"

    def action_l10n_ke_oscu_initialize(self):
        """ Initializing the device is necessary in order to receive the cmc key

        The cmc key is a token, necessary for all subsequent communication with the device.
        """
        self.ensure_one()
        session = requests.session()
        branch_code = self.l10n_ke_oscu_branch_code
        content = {
            'tin':       self.vat,                        # VAT No
            'bhfId':     branch_code,                        # Branch ID
            'dvcSrlNo':  self.l10n_ke_oscu_serial_number, # Device serial number
        }
        print(content) # TODO - remove print statements, use _logger debug or info

        url = urljoin(self._l10n_ke_oscu_get_base_url(), "selectInitOsdcInfo")
        response = session.post(url, json=content)
        print(response.content)
        response_content = response.json()
        print(f"\n\n response_content:\n{response_content}\n\n")
        if response.json()['resultCd'] != '000':
            raise ValidationError('Request Error Code: %s, Message: %s' % (response_content['resultCd'], response_content['resultMsg']))
        if response_content['resultCd'] == '000':
            info = response_content['data']['info']
            self.l10n_ke_oscu_cmc_key = info['cmcKey']
            self.l10n_ke_control_unit = info['sdcId']
            # TODO: check what is the best place to create the sequences automatically if already needed
            return True

    # TODO - action_l10n_ke_get_item_codes
    #        action_l10n_ke_get_stock_moves
    #        action_l10n_ke_create_branch_user
    #        action_l10n_ke_send_insurance
    #
    #        we need to figure out the functional justification for these right now they just
    #        facilitate buttons that allow us to pass certification with the KRA.
    #        If possible, it would be nice to remove them
    #        - regardless, if they remain, we need docstrings that at least describe what they're doing

    def action_l10n_ke_get_item_codes(self):
        content = {'lastReqDt': '20180301000000'}
        error, data, dummy = self._l10n_ke_call_etims('selectItemList', content)
        if error:
            raise UserError(error['message'])
        raise UserError(json.dumps(data, indent=4))

    def action_l10n_ke_get_stock_moves(self):
        content = {
            'lastReqDt': '20180301000000',
        }
        error, data, dummy = self._l10n_ke_call_etims('selectStockMoveList', content)
        if error:
            raise UserError(error['message'])
        raise UserError(json.dumps(data, indent=4))

    def action_l10n_ke_create_branch_user(self):
        user = self.env.user
        content = {
            'lastReqDt': '20180101000000',
            'userId': user.id,
            'userNm': user.login,
            'pwd': '1234',
            'useYn': "Y",
            "regrId": "Test",
            "regrNm": "Test", "modrId": "Test", "modrNm": "Test"
        }
        error, data, dummy = self._l10n_ke_call_etims('saveBhfUser', content)
        if error:
            raise UserError(error)

    def action_l10n_ke_send_insurance(self):
        content = {
            'isrccCd': self.l10n_ke_insurance_code,
            'isrccNm': self.l10n_ke_insurance_name,
            'isrcRt': self.l10n_ke_insurance_rate,
            'useYn': 'Y',
            **self._l10n_ke_get_user_dict(self.env.user, self.env.user),
        }
        error, data, dummy = self._l10n_ke_call_etims('saveBhfInsurance', content)
        if error:
            raise UserError(error['message'])

    def action_l10n_ke_create_branches(self): # TODO - docstring
        content = {'lastReqDt': '20180101000000'}
        error, data, dummy = self._l10n_ke_call_etims('selectBhfList', content)
        if error:
            raise UserError(error['message'])
        for bhf in data['bhfList']:
            if bhf['bhfId'] != self.l10n_ke_oscu_branch_code:
                company = self.search([('id', 'child_of', self.id), ('l10n_ke_oscu_branch_code', '=', bhf['bhfId'])], limit=1)
                if not company:
                    self.create({
                        'parent_id': self.id,
                        'name': bhf['bhfNm'],
                        'vat': bhf['tin'],
                        'l10n_ke_server_mode': self.l10n_ke_server_mode,
                        'l10n_ke_oscu_branch_code': bhf['bhfId'],
                        'state_id': self.env['res.country.state'].search([('country_id.code', '=', 'KE'), ('name', '=', bhf['prvncNm'])], limit=1).id,
                        'street': bhf['dstrtNm'],
                        'street2': bhf['sctrNm'],
                        'email': bhf['mgrEmail'],
                        'country_id': self.env.ref('base.ke').id,
                    })

    def _l10n_ke_oscu_get_session(self):
        """ Return a requests.session with the appropriate header fields for usage with the OSCU """
        session = requests.Session()
        session.headers.update({
            'tin': self.vat,
            'bhfid': self.l10n_ke_oscu_branch_code,
            'cmcKey': self.sudo().l10n_ke_oscu_cmc_key,
        })
        return session  # TODO - avoid leaking the Session object for security reasons

    def _l10n_ke_call_etims(self, urlext, content):
        """ Make a request to the OSCU

        :param string urlext: the extension of the url, represents the API endpoint to call.
        :param dict content:  represents the json content to be used in the request
        :returns: a tuple (dict errors, dict data, string result_date)
        """

        session = self._l10n_ke_oscu_get_session()
        url = urljoin(self._l10n_ke_oscu_get_base_url(), urlext)
        print(urlext)
        print(content) # testing purpose
        try:
            if self.l10n_ke_server_mode != 'demo':
                response = session.post(url, json=content)  # TODO - need to add timeout
            else:
                response = self._l10n_ke_get_demo_response(urlext, content)
            print(response.text)
        except (ValueError, requests.exceptions.ConnectionError, requests.exceptions.MissingSchema, requests.exceptions.Timeout, requests.exceptions.HTTPError) as e:
            _logger.exception("Exception occurred!")
            return {'code': 'CON', 'message':_('Connection Error: \n') + str(e)}, {}, "connection_error"

        try:
            response_dict = response.json()
        except JSONDecodeError:
            _logger.exception("Exception occurred!")
            return {'code': 'JSON', 'message': response.content}, {}, None

        if response_dict['resultCd'] == '000':
            return {}, response_dict['data'], response_dict['resultDt']
        else:
            return {'code': response_dict['resultCd'], 'message': response_dict['resultMsg']}, {}, response_dict['resultDt']

    def _l10n_ke_get_user_dict(self, create_user, write_user):
        """ Utility method to easily retrieve those dicts"""
        return {
            'regrId': create_user.id,
            'regrNm': create_user.name,
            'modrId': write_user.id,
            'modrNm': write_user.name,
        }

    def _l10n_ke_get_invoice_sequence(self, move_type='out_invoice'):
        """Returns the invoice sequence of a given company, and creates it if one is not yet defined."""
        self.ensure_one()
        sequence_code = 'l10n.ke.oscu.sale.sequence' if move_type.startswith('out_') else 'l10n.ke.oscu.purchase.sequence'

        if not (sequence := self.env['ir.sequence'].search([
            ('code', '=', sequence_code),
            ('company_id', '=', self.id),
        ])):
            sequence_name = 'eTIMS Customer Invoice Number' if move_type.startswith('out_') else 'eTIMS Vendor Bill Number'
            return self.env['ir.sequence'].create({
                'name': sequence_name,
                'implementation': 'no_gap',
                'company_id': self.id,
                'code': sequence_code,
            })
        return sequence

    def _l10n_ke_get_demo_response(self, urlext, content):
        class Response:
            def __init__(self, content):
                self.content = content
                self.text = content.decode()

            def json(self):
                return json.loads(self.content)

        stock_services = (
            'insertStockIO',
            'saveStockMaster',
            'selectImportItemList',
            'updateImportItem',
        )
        module = 'l10n_ke_edi_oscu_stock' if urlext in stock_services else 'l10n_ke_edi_oscu'

        response_files = {
            'insertTrnsPurchase': 'success',
            'insertStockIO': 'success',
            'saveBhfUser': 'success',
            'saveItem': 'success',
            'saveStockMaster': 'success',
            'saveTrnsSalesOsdc': 'save_sale_success',
            'selectBhfList': 'get_branches',
            'selectCodeList': 'get_codes',
            'selectImportItemList': 'get_imports_1',
            'selectTrnsPurchaseSalesList': 'get_purchases_1' if 'l10n_ke_oscu_last_fetch_customs_import_date' in self else 'get_purchases_2',
            'updateImportItem': 'success'
        }

        with file_open(f'{module}/tests/mocked_responses/{response_files[urlext]}.json', 'rb') as response_file:
            content = response_file.read()
        return Response(content)


class BaseDocumentLayout(models.TransientModel):
    _inherit = 'base.document.layout'

    @api.model
    def _default_company_details(self):
        """The KRA requires that the VAT number appears in the header of the document."""
        company_details = super()._default_company_details()
        if (company := self.env.company) and (vat := company.vat) and company.l10n_ke_oscu_is_active:
            return company_details + Markup(nl2br('\n' + f'KRA PIN: {company.vat}'))
        return company_details

    @api.model
    def _default_report_footer(self):
        if (company := self.env.company) and (vat := company.vat) and company.l10n_ke_oscu_is_active:
            footer_fields = [field for field in [company.phone, company.email, company.website] if isinstance(field, str) and len(field) > 0]
            return Markup(' ').join(footer_fields)
        return super()._default_report_footer()

    company_details = fields.Html(default=_default_company_details)
    report_footer = fields.Html(default=_default_report_footer)

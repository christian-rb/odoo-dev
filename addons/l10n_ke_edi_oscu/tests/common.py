# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import types
from unittest import mock
import contextlib
import requests
import logging

from odoo import Command
from odoo.tests import tagged
from odoo.tools.misc import file_open
from odoo.addons.account.tests.test_account_move_send import TestAccountMoveSendCommon

_logger = logging.getLogger(__name__)


class TestKeEdiCommon(TestAccountMoveSendCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref='ke'):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.is_live_test = False

        # cls.company_data['company'].write({
        #     'vat': 'B123456789F',
        #     'l10n_ke_oscu_branch_code': '00',
        #     'l10n_ke_oscu_cmc_key': 'test_cmc_key',
        #     'l10n_ke_oscu_serial_number': 'TESTSERIALNUMBER',
        # })
        cls.company_data['company'].write({
            'vat': 'P052112956W',
            'l10n_ke_oscu_branch_code': '00',
            'l10n_ke_server_mode': 'test',
            'l10n_ke_oscu_cmc_key': '71D825151F9B4F9DBA9D7390B211A329438BC9DD7ECB4F5A8BAD',
            'l10n_ke_oscu_serial_number': 'KRACU0300000164',
            'l10n_ke_control_unit': 'KRACU0300000164',
        })
        cls.partner_a.write({
            'name': 'Ralph Jr',
            'street': 'The Cucumber Lounge',
            'city': 'Vineland',
            'zip': '00500',
            'country_id': cls.env.ref('base.ke').id,
            'vat': 'A000123456F',
        })

        cls.standard_rate_sales_tax = cls.env.ref(f"account.{cls.company_data['company'].id}_ST16")
        cls.standard_rate_purchase_tax = cls.env.ref(f"account.{cls.company_data['company'].id}_PT16")
        cls.reduced_rate_sales_tax = cls.env.ref(f"account.{cls.company_data['company'].id}_ST8")
        cls.reduced_rate_purchase_tax = cls.env.ref(f"account.{cls.company_data['company'].id}_PT8")

        cls.product_service = cls.env['product.product'].create([{
            'name': 'Fiscal Optimization Consultancy',
            'type': 'service',
            'taxes_id': [Command.set(cls.standard_rate_sales_tax.ids)],
            'supplier_taxes_id': [Command.set(cls.standard_rate_purchase_tax.ids)],
            'standard_price': 100.0,
            'l10n_ke_product_type_code': '3',
            'l10n_ke_origin_country_id': cls.env.ref('base.ke').id,
            'unspsc_code_id': cls.env['product.unspsc.code'].search([
                ('code', '=', '81121500'),
            ], limit=1).id,
            'l10n_ke_packaging_unit_id': cls.env.ref('l10n_ke_edi_oscu.code_17_OU').id,
            'l10n_ke_packaging_quantity': 1,
        }])

    def _test_create_branches(self):
        parent = self.company_data['company']
        parent.action_l10n_ke_create_branches()
        branches = self.env['res.company'].search([('parent_id', '=', parent.id)])
        expected_branches = [
            {
                'name': 'KAKAMEGA',
                'vat': 'P052112956W',
                'l10n_ke_oscu_branch_code': '02',
            },
            {
                'name': 'MOMBASA',
                'vat': 'P052112956W',
                'l10n_ke_oscu_branch_code': '01',
            },
        ]
        self.assertRecordValues(branches, expected_branches)

        for branch in branches:
            branch.write({'country_id': self.env.ref('base.ke')})
            (self.product_a | self.product_b).with_company(branch).write({'standard_price': 30})

    def assertJsonDictEquals(self, json_test, json_expected):
        """Compare JSON dict structures

        Recursively traverse the dictionary ignoring the "___ignore___" case and comparing
        only the expected types.
        """

        if isinstance(json_test, list):
            self.assertEqual(len(json_test), len(json_expected),
                "Arrays have differing lengths. "
                "Expected a length of %i and got %i" % (len(json_expected), len(json_test))
            )
            for item, item_expected in zip(json_test, json_expected):
                self.assertJsonDictEquals(item, item_expected)

        if isinstance(json_test, dict):
            self.assertEqual(
                json_test.keys(), json_expected.keys(),
                "JSON dicts have differing keys:\n"
                "Keys present in test data but not expected: %s\n"
                "Keys expected but not found: %s." % (
                    ', '.join(set(json_test.keys()) - set(json_expected.keys())),
                    ', '.join(set(json_expected.keys()) - set(json_test.keys())),
                ),
            )

        for (key, val), (key_expected, val_expected) in zip(sorted(json_test.items()), sorted(json_expected.items())):

            if isinstance(val_expected, str) and val_expected == '___ignore___':
                continue

            self.assertTrue(isinstance(val, type(val_expected)), "Type of %s not equal: %s != %s" % (key,  val, val_expected))

            if isinstance(val, dict):
                self.assertJsonDictEquals(val, val_expected)

            if isinstance(val, (str, int, float, types.NoneType)):  # bool is a subclass of int
                self.assertEqual(val, val_expected, "Values of %s not equal: %s != %s" % (key, val, val_expected))

    @contextlib.contextmanager
    def patch_session(self, responses):
        """ Patch requests.Session in l10n_ke_edi_oscu/models/company.py """
        test_case = self
        json_module = json

        responses = iter(responses)

        class MockedSession:
            def __init__(self):
                self.headers = {}

            def post(self, url, json=None, timeout=None):
                expected_service, expected_request_filename, response_filename = next(responses)
                _, _, service = url.rpartition('/')

                test_case.assertEqual(service, expected_service)

                stock_services = (
                    'insertStockIO',
                    'saveStockMaster',
                    'selectImportItemList',
                    'updateImportItem',
                )

                module = 'l10n_ke_edi_oscu_stock' if service in stock_services else 'l10n_ke_edi_oscu'

                with file_open(f'{module}/tests/expected_requests/{expected_request_filename}.json', 'rb') as expected_request_file:
                    try:
                        test_case.assertJsonDictEquals(json, json_module.loads(expected_request_file.read()))
                    except AssertionError:
                        _logger.error('Unexpected request JSON for service %s', service)
                        raise

                mock_response = mock.Mock(spec=requests.Response)
                mock_response.status_code = 200
                mock_response.headers = ''

                with file_open(f'{module}/tests/mocked_responses/{response_filename}.json', 'rb') as response_file:
                    mock_response.content = response_file.read()
                    mock_response.text = mock_response.content.decode()

                mock_response.json.side_effect = lambda: json_module.loads(mock_response.content)

                return mock_response

        with mock.patch('odoo.addons.l10n_ke_edi_oscu.models.res_company.requests.Session', side_effect=MockedSession, autospec=True) as mock_session:
            yield mock_session

        try:
            next(responses)
        except StopIteration:
            pass
        else:
            test_case.fail('Not all expected calls were made!')

    @contextlib.contextmanager
    def patch_cron_trigger(self):
        """ Decorator for patching ir.cron.trigger so that the cron gets run right after this context manager's exit. """
        crons_to_trigger = []

        def mock_trigger(cron, at=None):
            crons_to_trigger.append(cron)

        with mock.patch.object(type(self.env['ir.cron']), '_trigger', side_effect=mock_trigger, autospec=True) as mocked_trigger:
            yield mocked_trigger

        # Run cron as current user (not superuser) to limit ourselves to the test company
        self.env['ir.cron'].union(*crons_to_trigger).ir_actions_server_id.run()

    def create_reversal(self, invoice, is_modify=False):
        """ Create a credit note that reverses an invoice. """
        wizard_vals = {'journal_id': invoice.journal_id.id}
        wizard_reverse = self.env['account.move.reversal'].with_context(active_ids=invoice.ids, active_model='account.move').create(wizard_vals)
        wizard_reverse.write({
            'reason': 'Return',
            'l10n_ke_reason_code_id': self.env.ref('l10n_ke_edi_oscu.code_32_06').id,
        })
        wizard_reverse.reverse_moves(is_modify=is_modify)
        return wizard_reverse.new_move_ids

    @contextlib.contextmanager
    def set_invoice_number(self, invoice):
        global last_invoice
        if not self.is_live_test:
            yield
            return
        else:
            if not invoice.move_type.startswith('out_'):
                raise Exception('`set_invoice_number` is only needed for out_invoice / out_refund!')
            try:
                last_invoice += 1
                sequence = invoice.company_id._l10n_ke_get_invoice_sequence(invoice.move_type)
                sequence.number_next_actual = last_invoice
                yield
            finally:
                if not invoice.l10n_ke_oscu_receipt_number:
                    last_invoice -= 1
                else:
                    with file_open('l10n_ke_edi_oscu/tests/common.py', 'a') as test_file:
                        test_file.write(f'last_invoice = {last_invoice}\n')


last_invoice = 320

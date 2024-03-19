from odoo import Command
from odoo.addons.account.tests.test_taxes_tax_totals_summary import TestRecordsTaxTotalsSummary
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestInvoiceTaxTotalsSummary(TestRecordsTaxTotalsSummary):
    allow_inherited_tests_method = True

    def create_invoice_from_document_values(self, document_values):
        if cash_rounding := document_values.get('cash_rounding'):
            cash_rounding_id = self.env['account.cash.rounding'].create({
                'name': 'Rounding HALF-UP',
                'rounding': cash_rounding['precision_rounding'],
                'strategy': cash_rounding['strategy'],
                'rounding_method': cash_rounding['rounding_method'],
                'profit_account_id': self.company_data['default_account_revenue'].id,
                'loss_account_id': self.company_data['default_account_expense'].id,
            }).id
        else:
            cash_rounding_id = None
        return self.env['account.move'].create({
            'move_type': 'out_invoice',
            'invoice_date': '2023-01-01',
            'invoice_cash_rounding_id': cash_rounding_id,
            'invoice_line_ids': [
                Command.create({
                    'name': 'line',
                    'display_type': 'product',
                    'price_unit': line['price_unit'],
                    'quantity': line['quantity'],
                    'discount': line['discount'],
                    'account_id': self.company_data['default_account_revenue'].copy().id,  # Force a != grouping key for tax lines.
                    'tax_ids': [Command.set([tax_data['id'] for tax_data in line['taxes_data']])],
                })
                for line in document_values['lines']
            ],
        })

    def _get_test_py_tax_totals_summary_results(self, document_values, exclude_tax_group_ids=None):
        # OVERRIDE
        # TODO: round_globally
        # if document_values['rounding_method'] == 'round_globally':
        #     return
        if exclude_tax_group_ids:
            return

        invoice = self.create_invoice_from_document_values(document_values)
        return invoice.tax_totals

    def test_tax_totals_with_company_currency_amounts(self):
        self.env['res.currency.rate'].create({
            'name': '2018-01-01',
            'rate': 0.2,
            'currency_id': self.currency_data['currency'].id,
        })

        tax_10 = self.percent_tax(10.0, tax_group_id=self.tax_groups[0].id)
        tax_20 = self.percent_tax(20.0, tax_group_id=self.tax_groups[1].id)

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
            'invoice_date': '2019-01-01',
            'currency_id': self.currency_data['currency'].id,
            'invoice_line_ids': [
                Command.create({
                    'name': 'line',
                    'display_type': 'product',
                    'account_id': self.company_data['default_account_revenue'].id,
                    'price_unit': amount,
                    'tax_ids': [Command.set(taxes.ids)],
                })
                for amount, taxes in [(100, tax_10), (300, tax_20)]
            ],
        })

        self._assert_sub_test_tax_totals_summary(
            {
                'expected_values': {
                    'same_tax_base': False,
                    'display_in_company_currency': True,
                    'currency_id': invoice.currency_id.id,
                    'untaxed_amount': 400.0,
                    'untaxed_amount_comp': 2000.0,
                    'tax_amount': 70.0,
                    'tax_amount_comp': 350.0,
                    'total_amount': 470.0,
                    'total_amount_comp': 2350.0,
                    'subtotals': [
                        {
                            'name': "Untaxed Amount",
                            'base': 400.0,
                            'base_comp': 2000.0,
                            'tax_amount': 70.0,
                            'tax_amount_comp': 350.0,
                            'tax_groups': [
                                {
                                    'id': self.tax_groups[0].id,
                                    'base': 100.0,
                                    'base_comp': 500.0,
                                    'tax_amount': 10.0,
                                    'tax_amount_comp': 50.0,
                                    'display_base': 100.0,
                                    'display_base_comp': 500.0,
                                    'group_name': self.tax_groups[0].name,
                                },
                                {
                                    'id': self.tax_groups[1].id,
                                    'base': 300.0,
                                    'base_comp': 1500.0,
                                    'tax_amount': 60.0,
                                    'tax_amount_comp': 300.0,
                                    'display_base': 300.0,
                                    'display_base_comp': 1500.0,
                                    'group_name': self.tax_groups[1].name,
                                },
                            ],
                        },
                    ],
                },
            },
            invoice.tax_totals,
        )

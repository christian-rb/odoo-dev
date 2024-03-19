from odoo import Command
from odoo.addons.account.tests.test_taxes_tax_totals_summary import TestRecordsTaxTotalsSummary
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestSaleTaxTotalsSummary(TestRecordsTaxTotalsSummary):
    allow_inherited_tests_method = True

    def create_so_from_document_values(self, document_values):
        return self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
            'order_line': [
                Command.create({
                    'name': 'line',
                    'product_id': self.product_a.id,
                    'price_unit': line['price_unit'],
                    'product_uom_qty': line['quantity'],
                    'discount': line['discount'],
                    'tax_id': [Command.set([tax_data['id'] for tax_data in line['taxes_data']])],
                })
                for line in document_values['lines']
            ],
        })

    def _get_test_py_tax_totals_summary_results(self, document_values, exclude_tax_group_ids=None):
        # OVERRIDE
        # Cash rounding is not available on sale orders.
        if exclude_tax_group_ids or document_values.get('cash_rounding'):
            return

        so = self.create_so_from_document_values(document_values)
        return so.tax_totals

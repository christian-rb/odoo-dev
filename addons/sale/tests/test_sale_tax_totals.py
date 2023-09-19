# -*- coding: utf-8 -*-
from odoo.addons.account.tests.test_invoice_tax_totals import TestTaxTotals
from odoo.fields import Command
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class SaleTestTaxTotals(TestTaxTotals):

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.so_product = cls.env['product.product'].create({
            'name': 'Odoo course',
            'type': 'service',
        })

    def _create_document_for_tax_totals_test(self, lines_data):
        # Overridden in order to run the inherited tests with sale.order's
        # tax_totals field instead of account.move's

        lines_vals = [
            (0, 0, {
                'name': 'test',
                'product_id': self.so_product.id,
                'price_unit': amount,
                'product_uom_qty': 1,
                'tax_id': [(6, 0, taxes.ids)],
            })
        for amount, taxes in lines_data]

        return self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
            'order_line': lines_vals,
        })

    def test_action_recompute_taxes(self):
        '''
        This test verifies the taxes recomputation action that can be triggered
        after updating the fiscal position on a sale order document.
        '''
        special_tax = self.env['account.tax'].create({
            'name': "special_tax_10",
            'amount_type': 'percent',
            'amount': 25.0,
            'tax_group_id': self.tax_group1.id,
            'include_base_amount': True,
            'price_include': True,
        })

        mapped_tax_a = self.env['account.tax'].create({
            'name': "tax_a",
            'amount_type': 'percent',
            'amount': 12.5,
            'tax_group_id': self.tax_group1.id,
            'include_base_amount': True,
            'price_include': True,
        })

        mapped_tax_b = self.env['account.tax'].create({
            'name': "tax_b",
            'amount_type': 'percent',
            'amount': 5.0,
            'tax_group_id': self.tax_group1.id,
            'include_base_amount': True,
            'price_include': True,
        })

        sales_tax = self.env['account.tax'].create({
            'name': "VAT 20%",
            'amount_type': 'percent',
            'amount': 20.0,
            'tax_group_id': self.tax_group1.id,
            'price_include': True,
        })

        mapping_a = self.env['account.fiscal.position'].create({
            'name': 'Special Tax Reduction',
            'tax_ids': [Command.create({'tax_src_id': special_tax.id, 'tax_dest_id': mapped_tax_a.id})],
        })
        mapping_b = self.env['account.fiscal.position'].create({
            'name': 'Special Tax Reduction',
            'tax_ids': [Command.create({'tax_src_id': special_tax.id, 'tax_dest_id': mapped_tax_b.id})],
        })

        # taxes and standard price need to be set on the product, as they will be
        # recomputed when changing the fiscal position.
        self.so_product.write({
            'lst_price': 300,
            'taxes_id': [Command.set((special_tax + sales_tax).ids)],
        })

        document = self._create_document_for_tax_totals_test([
            (300, special_tax + sales_tax),
        ])

        self.assertEqual(document.amount_total, 300)
        self.assertEqual(document.amount_tax, 100)
        document.fiscal_position_id = mapping_a
        document.action_update_taxes()
        self.assertEqual(document.amount_total, 270)
        self.assertEqual(document.amount_tax, 70)
        document.fiscal_position_id = mapping_b
        document.action_update_taxes()
        self.assertEqual(document.amount_total, 252)
        self.assertEqual(document.amount_tax, 52)

from odoo import fields, Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged('post_install', '-at_install', 'post_install_l10n')
class TestTdsTcsAlert(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass(chart_template_ref='in')

        # ==== Tax Groups ====
        cls.tax_group_tcs_sale_1 = cls.env['account.tax.group'].create({
            'name': 'TCS - 206a',
            'l10_in_is_threshold': True,
            'l10n_in_consider_tax': 'total_amount',
            'l10n_in_is_per_transection_limit': True,
            'l10n_in_per_transection_limit': 30000.0,
            'l10n_in_is_aggregate_limit': True,
            'l10n_in_aggregate_limit': 100000.0,
        })

        cls.tax_group_tds_purchase_1 = cls.env['account.tax.group'].create({
            'name': 'TDS - 194a',
            'l10_in_is_threshold': True,
            'l10n_in_is_per_transection_limit': True,
            'l10n_in_per_transection_limit': 18000.0,
            'l10n_in_is_aggregate_limit': True,
            'l10n_in_aggregate_limit': 50000.0,
        })

        cls.tax_group_tcs_sale_2 = cls.env['account.tax.group'].create({
            'name': 'TCS - 206b',
            'l10_in_is_threshold': True,
            'l10n_in_consider_tax': 'total_amount',
            'l10n_in_is_per_transection_limit': True,
            'l10n_in_per_transection_limit': 20000.0,
            'l10n_in_is_aggregate_limit': False,
        })

        cls.tax_group_tds_purchase_2 = cls.env['account.tax.group'].create({
            'name': 'TDS - 194b',
            'l10_in_is_threshold': True,
            'l10n_in_is_per_transection_limit': True,
            'l10n_in_per_transection_limit': 25000.0,
            'l10n_in_is_aggregate_limit': False,
        })

        cls.tax_group_tcs_sale_3 = cls.env['account.tax.group'].create({
            'name': 'TCS - 206c',
            'l10_in_is_threshold': True,
            'l10n_in_consider_tax': 'total_amount',
            'l10n_in_is_per_transection_limit': False,
            'l10n_in_is_aggregate_limit': True,
            'l10n_in_aggregate_limit': 50000.0,
        })

        cls.tax_group_tds_purchase_3 = cls.env['account.tax.group'].create({
            'name': 'TDS - 194c',
            'l10_in_is_threshold': True,
            'l10n_in_is_per_transection_limit': False,
            'l10n_in_is_aggregate_limit': True,
            'l10n_in_aggregate_limit': 50000.0,
        })

        # ==== Chart of Accounts ====
        cls.sale_account_1 = cls.env['account.account'].create({
            'code': 'sale.account.1',
            'name': 'sale_account_1',
            'account_type': 'income',
            'company_id': cls.company_data['company'].id,
            'l10n_in_tds_tcs_section': cls.tax_group_tcs_sale_1.id,
        })

        cls.sale_account_2 = cls.env['account.account'].create({
            'code': 'sale.account.2',
            'name': 'sale_account_2',
            'account_type': 'income',
            'company_id': cls.company_data['company'].id,
            'l10n_in_tds_tcs_section': cls.tax_group_tcs_sale_2.id,
        })

        cls.purchase_account_1 = cls.env['account.account'].create({
            'code': 'purchase.account.1',
            'name': 'purchase_account_1',
            'account_type': 'expense',
            'company_id': cls.company_data['company'].id,
            'l10n_in_tds_tcs_section': cls.tax_group_tds_purchase_1.id,
        })

        cls.purchase_account_1_c2 = cls.env['account.account'].create({
            'code': 'purchase.account.1',
            'name': 'purchase_account_1',
            'account_type': 'expense',
            'company_id': cls.company_data_2['company'].id,
            'l10n_in_tds_tcs_section': cls.tax_group_tds_purchase_1.id,
        })

        country_in_id = cls.env.ref("base.in").id

        # ==== Partners ====
        cls.partner_c = cls.env['res.partner'].create({
            'name': 'partner_c',
            'property_payment_term_id': cls.pay_terms_a.id,
            'property_supplier_payment_term_id': cls.pay_terms_a.id,
            'property_account_receivable_id': cls.company_data['default_account_receivable'].id,
            'property_account_payable_id': cls.company_data['default_account_payable'].id,
            'company_id': False,
            'vat': '27DJMPM8965E1ZE',
            'l10n_in_pan': 'DJMPM8965E',
            'l10n_in_gst_treatment': 'regular',
            'country_id': country_in_id,
        })

        cls.partner_d = cls.env['res.partner'].create({
            'name': 'partner_d',
            'property_payment_term_id': cls.pay_terms_a.id,
            'property_supplier_payment_term_id': cls.pay_terms_a.id,
            'property_account_receivable_id': cls.company_data['default_account_receivable'].id,
            'property_account_payable_id': cls.company_data['default_account_payable'].id,
            'company_id': False,
            'vat': '23DJMPM8965E1ZT',
            'l10n_in_pan': 'DJMPM8965E',
            'l10n_in_gst_treatment': 'regular',
            'country_id': country_in_id,
        })

        # ==== Company ====
        cls.company_data["company"].write({
            "vat": "24AAGCC7144L6ZJ",
            "l10n_in_pan": "AAGCC7144L",
            "state_id": cls.env.ref("base.state_in_gj").id,
            "street": "street1",
            "city": "city1",
            "zip": "123456",
            "country_id": country_in_id,
        })

        cls.company_data_2["company"].write({
            "vat": "27AAGCC7144L6ZU",
            "l10n_in_pan": "AAGCC7144L",
            "state_id": cls.env.ref("base.state_in_gj").id,
            "street": "street1",
            "city": "city1",
            "zip": "123456",
            "country_id": country_in_id,
        })

        # ==== Products ====
        cls.product_1 = cls.env['product.product'].create({
            'name': 'product_1',
            'uom_id': cls.env.ref('uom.product_uom_unit').id,
            'lst_price': 1000.0,
            'standard_price': 800.0,
            'property_account_income_id': cls.sale_account_1.id,
            'property_account_expense_id': cls.purchase_account_1.id,
            'taxes_id': []
        })

        cls.product_2 = cls.env['product.product'].create({
            'name': 'product_2',
            'uom_id': cls.env.ref('uom.product_uom_unit').id,
            'lst_price': 2000.0,
            'standard_price': 1600.0,
            'property_account_income_id': cls.sale_account_1.id,
            'property_account_expense_id': cls.purchase_account_1.id,
            'taxes_id': []
        })

    def test_compute_tcs_tds_warning(self):
        '''
        Test that if the per transaction limit is not exceeded,
        the alert should not be set.
        '''
        move = self.env['account.move'].create({
            'partner_id': self.partner_c.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_1.id,
                    'quantity': 1,
                    'account_id': self.sale_account_1.id,
                    'price_unit': 1000,
                }),
            ],
        })
        move.action_post()
        # Check if the warning is correctly set
        self.assertEqual(move.l10n_in_tcs_tds_warning, False)

    def test_compute_tcs_tds_warning_if_per_transection_limit_crossed(self):
        '''
        Test that if the per transaction limit is exceeded in case of invoice,
        the warning message should be set accordingly.
        '''
        move = self.env['account.move'].create({
            'partner_id': self.partner_c.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_1.id,
                    'quantity': 40,
                    'account_id': self.sale_account_1.id,
                    'price_unit': 1000,
                }),
            ],
        })
        move.action_post()

        # Check if the warning is correctly set
        self.assertEqual(move.l10n_in_tcs_tds_warning, "It's advisable to collect TCS u/s  206a on this transaction.")

    def test_compute_tcs_tds_warning_if_aggregate_limit_crossed(self):
        '''
        Test that if the aggregate limit is exceeded in case of invoice,
        the warning message should be set accordingly.
        '''
        self.sale_account_1.write({
            'l10n_in_tds_tcs_section': self.tax_group_tcs_sale_3.id
        })
        # Create a move in 'posted' state
        move = self.env['account.move'].create({
            'partner_id': self.partner_c.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_1.id,
                    'quantity': 20,
                    'account_id': self.sale_account_1.id,
                    'price_unit': 1000,
                }),
            ],
        })
        move.action_post()

        move1 = self.env['account.move'].create({
            'partner_id': self.partner_c.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_1.id,
                    'quantity': 20,
                    'account_id': self.sale_account_1.id,
                    'price_unit': 1000,
                }),
            ],
        })
        move1.action_post()

        move2 = self.env['account.move'].create({
            'partner_id': self.partner_c.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_1.id,
                    'quantity': 20,
                    'account_id': self.sale_account_1.id,
                    'price_unit': 1000,
                }),
            ],
        })
        move2.action_post()

        # Check if the warning is correctly set
        self.assertEqual(move2.l10n_in_tcs_tds_warning, "It's advisable to collect TCS u/s  206c on this transaction.")

    def test_compute_tcs_tds_warning_multiple_products(self):
        '''
        Test that if there are multiple products in the move line,
        the warning message should be set accordingly.
        '''
        move = self.env['account.move'].create({
            'partner_id': self.partner_c.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_1.id,
                    'quantity': 20,
                    'account_id': self.sale_account_1.id,
                    'price_unit': 1000,
                }),
                Command.create({
                    'product_id': self.product_2.id,
                    'quantity': 10,
                    'account_id': self.sale_account_1.id,
                    'price_unit': 2000,
                }),
            ],
        })
        move.action_post()

        # Check if the warning is correctly set
        self.assertEqual(move.l10n_in_tcs_tds_warning, "It's advisable to collect TCS u/s  206a on this transaction.")

    def test_compute_tcs_tds_warning_removed_if_tex_available(self):
        '''
        Test that if a tax is added to the move line with a similar tax group
        as the account, the warning message should be removed.
        '''
        self.tax_sale_a.write({
            'tax_group_id': self.tax_group_tcs_sale_1.id,
        })
        # Create a move in 'posted' state
        move = self.env['account.move'].create({
            'partner_id': self.partner_c.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_1.id,
                    'quantity': 60,
                    'account_id': self.sale_account_1.id,
                    'tax_ids': [Command.set(self.tax_sale_a.ids)],
                    'price_unit': 1000,
                }),
            ],
        })
        move.action_post()

        # Check if the warning is correctly set
        self.assertEqual(move.l10n_in_tcs_tds_warning, False)

    def test_compute_tcs_tds_warning_if_some_lines_not_have_tax(self):
        '''
        Test that if there are multiple products in the move line and some of them
        don't have tax which have the same tax group as the account,
        the warning message should still be set accordingly.
        '''
        self.tax_sale_a.write({
            'tax_group_id': self.tax_group_tcs_sale_1.id,
        })
        move = self.env['account.move'].create({
            'partner_id': self.partner_d.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_1.id,
                    'quantity': 20,
                    'account_id': self.sale_account_1.id,
                    'tax_ids': [Command.set(self.tax_sale_a.ids)],
                    'price_unit': 1000,
                }),
                Command.create({
                    'product_id': self.product_2.id,
                    'quantity': 40,
                    'account_id': self.sale_account_1.id,
                    'price_unit': 2000,
                }),
            ],
        })
        move.action_post()

        # Check if the warning is correctly set
        self.assertEqual(move.l10n_in_tcs_tds_warning, "It's advisable to collect TCS u/s  206a on this transaction.")

    def test_compute_tcs_tds_warning_if_lines_have_multiple_accounts(self):
        '''
        Test that if there are multiple products in the move line and some of them
        have different accounts which have the different tax group as the account,
        the warning message should still be set accordingly.
        '''
        move = self.env['account.move'].create({
            'partner_id': self.partner_d.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_1.id,
                    'quantity': 40,
                    'account_id': self.sale_account_2.id,
                    'price_unit': 1000,
                }),
                Command.create({
                    'product_id': self.product_2.id,
                    'quantity': 40,
                    'account_id': self.sale_account_2.id,
                    'price_unit': 2000,
                }),
            ],
        })
        move.action_post()

        # Check if the warning is correctly set
        self.assertEqual(move.l10n_in_tcs_tds_warning, "It's advisable to collect TCS u/s  206b on this transaction.")

    def test_compute_tcs_tds_warning_if_lines_have_multiple_accounts_some_have_tax(self):
        '''
        Test that if there are multiple products in the move line and some of them
        have different accounts and some of them don't have tax which have the same
        tax group as the account, the warning message should still be set accordingly.
        '''
        self.tax_sale_a.write({
            'tax_group_id': self.tax_group_tcs_sale_1.id,
        })
        move = self.env['account.move'].create({
            'partner_id': self.partner_d.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_1.id,
                    'quantity': 40,
                    'account_id': self.sale_account_1.id,
                    'tax_ids': [Command.set(self.tax_sale_a.ids)],
                    'price_unit': 1000,
                }),
                Command.create({
                    'product_id': self.product_2.id,
                    'quantity': 40,
                    'account_id': self.sale_account_2.id,
                    'price_unit': 2000,
                }),
            ],
        })
        move.action_post()

        # Check if the warning is correctly set
        self.assertEqual(move.l10n_in_tcs_tds_warning, "It's advisable to collect TCS u/s  206b on this transaction.")

    def test_compute_tcs_tds_warning_bill(self):
        '''
        Test that if the per transaction limit is exceeded in case of bill,
        the warning message should be set accordingly.
        '''
        move = self.env['account.move'].create({
            'partner_id': self.partner_c.id,
            'move_type': 'in_invoice',
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_2.id,
                    'quantity': 20,
                    'account_id': self.purchase_account_1.id,
                    'price_unit': 1000,
                }),
            ],
        })

        move.action_post()

        # Check if the warning is correctly set
        self.assertEqual(move.l10n_in_tcs_tds_warning, "It's advisable to deduct TDS u/s  194a on this transaction.")

    def test_compute_tcs_tds_warning_bill_if_tax(self):
        '''
        Test that if a tax is added to the move line with a similar tax group
        as the account in case of bill, the warning message should be removed.
        '''
        self.tax_purchase_a.write({
            'tax_group_id': self.tax_group_tds_purchase_1.id,
        })
        # Create a move in 'posted' state
        move = self.env['account.move'].create({
            'partner_id': self.partner_d.id,
            'move_type': 'in_invoice',
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_2.id,
                    'quantity': 20,
                    'account_id': self.purchase_account_1.id,
                    'tax_ids': [Command.set(self.tax_purchase_a.ids)],
                    'price_unit': 1000,
                }),
            ],
        })
        move.action_post()

        # Check if the warning is correctly set
        self.assertEqual(move.l10n_in_tcs_tds_warning, False)

    def test_aggregate_total_calculation(self):
        move = self.env['account.move'].create({
            'partner_id': self.partner_c.id,
            'move_type': 'in_invoice',
            'invoice_date': fields.Date.today(),
            'company_id': self.company_data['company'].id,
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_2.id,
                    'quantity': 10,
                    'account_id': self.purchase_account_1.id,
                    'price_unit': 1500,
                }),
            ],
        })
        move.action_post()

        move1 = self.env['account.move'].create({
            'partner_id': self.partner_d.id,
            'move_type': 'in_invoice',
            'invoice_date': fields.Date.today(),
            'company_id': self.company_data['company'].id,
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_2.id,
                    'quantity': 10,
                    'account_id': self.purchase_account_1.id,
                    'price_unit': 1500,
                }),
            ],
        })
        move1.action_post()
        aggregate_total = move1._l10n_in_calculate_aggregate_total(self.partner_d.l10n_in_pan, self.company_data['company'].l10n_in_pan)
        tax_group_id = self.tax_group_tds_purchase_1
        self.assertEqual(aggregate_total[tax_group_id], 30000)

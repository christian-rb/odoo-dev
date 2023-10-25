# -*- coding: utf-8 -*-
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests.common import tagged


@tagged('post_install', '-at_install')
class TestAccountReimbursement(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

    def test_reimburse_full_payment_at_once(self):
        pass

    def test_reimburse_full_payment_in_two_times(self):
        pass

    def test_reimburse_partial_payment_at_once(self):
        pass

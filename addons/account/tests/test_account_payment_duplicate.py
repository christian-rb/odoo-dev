from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestAccountPaymentDuplicateMoves(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass()

        cls.receivable = cls.company_data['default_account_receivable']
        cls.payable = cls.company_data['default_account_payable']
        cls.bank_journal = cls.company_data['default_journal_bank']
        cls.comp_curr = cls.company_data['currency']
        cls.payment_in = cls.env['account.payment'].create({
            'amount': 50.0,
            'payment_type': 'inbound',
            'partner_id': cls.partner_a.id,
            'destination_account_id': cls.receivable.id,
        })
        cls.payment_out = cls.env['account.payment'].create({
            'amount': 50.0,
            'payment_type': 'outbound',
            'partner_id': cls.partner_a.id,
            'destination_account_id': cls.payable.id,
        })

    def test_duplicate_payments(self):
        """
            Ensure duplicated payments are computed correctly for both inbound and outbound payments.
            For it to be a duplicate, the partner, the date and the amount must be the same.
        """
        payment_in_1 = self.payment_in
        payment_out_1 = self.payment_out

        # Different type but same partner, amount and date, no duplicate
        self.assertRecordValues(payment_in_1, [{'duplicate_move_ids': []}])

        # Create duplicate payments
        payment_in_2 = payment_in_1.copy(default={'date': payment_in_1.date})
        payment_out_2 = payment_out_1.copy(default={'date': payment_out_1.date})
        # Inbound payment finds duplicate inbound payment, not the outbound payment with same information
        self.assertRecordValues(payment_in_2, [{
            'duplicate_move_ids': [payment_in_1.move_id.id],
        }])
        # Outbound payment finds duplicate outbound duplicate, not the inbound payment with same information
        self.assertRecordValues(payment_out_2, [{
            'duplicate_move_ids': [payment_out_1.move_id.id],
        }])
        # Different date but same amount and same partner, no duplicate
        payment_out_3 = payment_out_1.copy(default={'date': '2023-12-31'})
        self.assertRecordValues(payment_out_3, [{'duplicate_move_ids': []}])

        # Different amount but same partner and same date, no duplicate
        payment_out_4 = self.env['account.payment'].create({
            'amount': 60.0,
            'payment_type': 'outbound',
            'partner_id': self.partner_a.id,
            'destination_account_id': self.payable.id,
        })
        self.assertRecordValues(payment_out_4, [{'duplicate_move_ids': []}])

        # Different partner but same amount and same date, no duplicate
        payment_out_5 = self.env['account.payment'].create({
            'amount': 50.0,
            'payment_type': 'outbound',
            'partner_id': self.partner_b.id,
            'destination_account_id': self.payable.id,
        })
        self.assertRecordValues(payment_out_5, [{'duplicate_move_ids': []}])

    def test_payment_duplicate_moves(self):
        """
            Ensure payments with matching moves are computed correctly,
            including journal entries, refunds and statement lines.
            For it to be a duplicate, the partner, the date, the amount and the account
            (except for bank statement lines) must be the same.
        """
        payment_in_1 = self.payment_in
        payment_out_1 = self.payment_out

        # Create statement lines with positive value (inbound payment) and negative value (outbound payment)
        statement_line_in = self.env['account.bank.statement.line'].create({
            'date': payment_in_1.date,
            'journal_id': self.bank_journal.id,
            'payment_ref': 'line_1_in',
            'partner_id': self.partner_a.id,
            'amount': 50.0,
        })
        statement_line_out = self.env['account.bank.statement.line'].create({
            'date': payment_out_1.date,
            'journal_id': self.bank_journal.id,
            'payment_ref': 'line_1_out',
            'partner_id': self.partner_a.id,
            'amount': -50.0,
        })

        # Create credit note and refund with same amount, partner and date.
        credit_note = self.init_invoice('out_refund', amounts=[50.0], invoice_date=payment_in_1.date, partner=self.partner_a)
        refund = self.init_invoice('in_refund', amounts=[50.0], invoice_date=payment_in_1.date, partner=self.partner_a)

        # create_line_for_reconciliation allows creation of an entry on a specific account. The duplicate moves function
        # matches credits in a receivable acc or debits in a payable acc, which are the parameters in the helper function
        # Payment in = credit in a receivable account, hence the negative balance.
        misc_entry_in = self.create_line_for_reconciliation(-50.0, -50.0, self.comp_curr, payment_in_1.date, self.receivable, self.partner_a)
        misc_entry_out = self.create_line_for_reconciliation(50.0, 50.0, self.comp_curr, payment_in_1.date, self.payable, self.partner_a)

        # Inbound payment finds statement line, credit note and misc entry crediting receivable account
        self.assertRecordValues(payment_in_1, [{
            'duplicate_move_ids': (statement_line_in.move_id + credit_note + misc_entry_in.move_id).ids,
        }])
        # Outbound payment finds statement line, refund and misc entry debiting payable account
        self.assertRecordValues(payment_out_1, [{
            'duplicate_move_ids': (statement_line_out.move_id + refund + misc_entry_out.move_id).ids,
        }])

    def test_in_payment_multiple_duplicate_reference_batch(self):
        """ Ensure duplicated payments are computed correctly even when updated in batch """
        payment_1 = self.payment_in
        payment_2 = payment_1.copy(default={'date': payment_1.date})
        payment_3 = payment_1.copy(default={'date': payment_1.date})

        payments = payment_1 + payment_2 + payment_3

        self.assertRecordValues(payments, [
            {'duplicate_move_ids': (payment_2.move_id + payment_3.move_id).ids},
            {'duplicate_move_ids': (payment_1.move_id + payment_3.move_id).ids},
            {'duplicate_move_ids': (payment_1.move_id + payment_2.move_id).ids},
        ])

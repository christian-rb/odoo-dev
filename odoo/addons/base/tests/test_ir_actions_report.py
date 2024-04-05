from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestIrActionsReport(AccountTestInvoicingCommon):

    def setup(self):
        super().setup()
        self.first_invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'date': '2024-01-01',
            'invoice_date': '2024-01-01',
            'partner_id': self.partner_a.id,
            'invoice_line_ids': [Command.create({
                'name': 'Something',
                'quantity': 1,
                'price_unit': 123,
                'product_id': self.product_a.id
            })]
        })

        self.second_invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'date': '2024-01-01',
            'invoice_date': '2024-01-01',
            'partner_id': self.partner_a.id,
            'invoice_line_ids': [Command.create({
                'name': 'Something',
                'quantity': 1,
                'price_unit': 123,
                'product_id': self.product_a.id
            })]
        })

        self.third_invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'date': '2024-01-01',
            'invoice_date': '2024-01-01',
            'partner_id': self.partner_a.id,
            'invoice_line_ids': [Command.create({
                'name': 'Something',
                'quantity': 1,
                'price_unit': 123,
                'product_id': self.product_a.id
            })]
        })

    def test_report_with_some_resources_reloaded_from_attachment(self):
        """
        Test for opw-3827700, which caused reports generated for multiple invoices to fail if there was an invoice in
        the middle that had an attachment, and 'Reload from attachment' was enabled for the report. The misbehavior was
        caused by an indexing issue.
        """

        self.assert_invoice_creation((self.first_invoice + self.second_invoice + self.third_invoice),
                                     self.second_invoice)

    def test_report_with_some_resources_reloaded_from_attachment_with_multiple_page_invoice(self):
        """
        Same as @test_report_with_some_resources_reloaded_from_attachment, but tests the behavior for invoices that
        span multiple pages.
        """
        self.third_invoice.invoice_line_ids = [Command.create({
            'name': f'Something #{i}',
            'quantity': 1,
            'price_unit': 123,
            'product_id': self.product_a.id
        }) for i in range(50)]  # Make this a multipage invoice.

        self.assert_invoice_creation((self.first_invoice + self.second_invoice + self.third_invoice),
                                     self.second_invoice)

    def assert_invoice_creation(self, invoices, invoice_to_report):
        self.assertIn(invoice_to_report, invoices, "Invoice to report must be in invoices list")

        # Post invoices to be able to associate attachments.
        invoices.action_post()

        invoices_report_ref = 'account.report_invoice_with_payments'
        reports = self.env['ir.actions.report'].with_context(force_report_rendering=True)

        # Make sure attachments are created.
        invoices_report = reports._get_report(invoices_report_ref)
        if not invoices_report.attachment:
            invoices_report.attachment = "(object.state == 'posted') and ((object.name or 'INV').replace('/','_')+'.pdf')"
        invoices_report.attachment_use = True

        # Generate report for second invoice to create an attachment.
        second_invoice_report_content, content_type = reports._render_qweb_pdf(invoices_report_ref,
                                                                               res_ids=invoice_to_report.id)
        self.assertEqual(content_type, "pdf", "Report is not a PDF")
        self.assertTrue(second_invoice_report_content, "PDF not generated")

        # Make sure the attachment is created.
        invoices_report = reports._get_report(invoices_report_ref)
        self.assertTrue(invoices_report.retrieve_attachment(invoice_to_report), "Attachment not generated")

        aggregate_report_content, content_type = reports._render_qweb_pdf(invoices_report_ref, res_ids=invoices.ids)
        self.assertEqual(content_type, "pdf", "Report is not a PDF")
        self.assertTrue(aggregate_report_content, "PDF not generated")

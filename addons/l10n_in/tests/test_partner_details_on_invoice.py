from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged
import logging

_logger = logging.getLogger(__name__)

@tagged('post_install_l10n', 'post_install', '-at_install')
class TestReports(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref="in"):
        super().setUpClass(chart_template_ref=chart_template_ref)
        country_in_id = cls.env.ref("base.in").id
        cls.company_data["company"].write({
            "vat": "24AAGCC7144L6ZE",
            "state_id": cls.env.ref("base.state_in_gj").id,
            "street": "street1",
            "city": "city1",
            "zip": "123456",
            "country_id": country_in_id,
        })
        cls.env.company = cls.company_data["company"]
        cls.partner_a.write({
            'vat': '27DJMPM8965E1ZE',
            'l10n_in_gst_treatment':'regular',
            'state_id': cls.env.ref("base.state_in_mh"),
            'country_id':country_in_id,
        })
        cls.partner_b.write({
            'vat': '24ABCPM8965E1ZE',
            'l10n_in_gst_treatment':'composition',
            'state_id': cls.env.ref("base.state_in_hp"),
            'country_id':country_in_id,
        })
        cls.partner_c = cls.env['res.partner'].create({
            'name': "Overseas partner",
            'l10n_in_gst_treatment':'overseas',
            'state_id': cls.env.ref("base.state_us_1").id,
            'country_id': cls.env.ref("base.us").id,
            'zip': "123456",
        })
        cls.igst_sale_18 = cls.env['account.chart.template'].ref('igst_sale_18')

    def test_partner_details_change_with_invoice(self):
        invoice_1 = self.init_invoice(
            move_type='out_invoice',
            partner=self.partner_a,
            amounts=[125, 300, 404],
            taxes=[self.igst_sale_18]
        )
        invoice_2 = self.init_invoice(
            move_type='out_invoice',
            partner=self.partner_a,
            amounts=[250, 600],
            taxes=[self.igst_sale_18],
            post=True
        )
        # Place of Supply (pos) is same as of state of partner (for journal type sale)
        expected_pos_id = self.env.ref("base.state_in_mh").id
        self.assertRecordValues(
            invoice_1,
            [{
                'state': 'draft',
                'l10n_in_gst_treatment': self.partner_a.l10n_in_gst_treatment,
                'l10n_in_state_id': expected_pos_id,
            }]
        )
        self.assertRecordValues(
            invoice_2,
            [{
                'state': 'posted',
                'l10n_in_gst_treatment': self.partner_a.l10n_in_gst_treatment,
                'l10n_in_state_id': expected_pos_id,
            }]
        )
        self.partner_a.write({
            'vat': False,
            'l10n_in_gst_treatment': 'unregistered',
            'state_id': self.env.ref("base.state_in_tn"), # change state of partner
        })
        self.assertRecordValues(
            invoice_1,
            [{
                'state': 'draft',
                'l10n_in_gst_treatment': self.partner_a.l10n_in_gst_treatment,
                'l10n_in_state_id': expected_pos_id, # POS doesn't change unless the partner changes
            }]
        )
        self.assertRecordValues(
            invoice_2,
            [{ # check gst treatment and pos doesn't change on posted invoice
                'state': 'posted',
                'l10n_in_gst_treatment': 'regular',
            }]
        )
        invoice_2.button_draft()
        self.assertRecordValues(invoice_2, [{
            'state': 'draft',
            'l10n_in_gst_treatment': self.partner_a.l10n_in_gst_treatment,
            'l10n_in_state_id': expected_pos_id,
        }])

    def test_partner_change_with_invoice(self):
        out_invoice = self.init_invoice(
            move_type='out_invoice',
            partner=self.partner_b,
            amounts=[40, 160, 25],
            taxes=[self.igst_sale_18]
        )
        in_invoice = self.init_invoice(
            move_type='in_invoice',
            partner=self.partner_a,
            amounts=[452, 58, 110],
            taxes=[self.igst_sale_18],
        )

        self.assertRecordValues(
            out_invoice,
            [{
                'state': 'draft',
                'l10n_in_gst_treatment': self.partner_b.l10n_in_gst_treatment,
                'l10n_in_state_id': self.env.ref("base.state_in_hp").id,
            }]
        )
        out_invoice.partner_id = self.partner_c
        self.assertRecordValues(
            out_invoice,
            [{
                'state': 'draft',
                'l10n_in_gst_treatment': self.partner_c.l10n_in_gst_treatment,
                'l10n_in_state_id': self.env.ref("l10n_in.state_in_oc").id,
            }]
        )
        self.assertRecordValues(
            in_invoice,
            [{
                'state': 'draft',
                'l10n_in_gst_treatment': self.partner_a.l10n_in_gst_treatment,
                'l10n_in_state_id': self.env.company.state_id.id,
            }]
        )

    def test_place_of_supply(self):
        # ==== Partners ====
        test_partner_1 = self.env['res.partner'].create({
            'company_id': self.env.company.id,
            'name': 'Partner 1',
            'company_type': 'company',
            'country_id': self.env.ref("base.in").id,
            'state_id': self.env.ref('base.state_in_hp').id,
        })

        test_partner_2 = self.env['res.partner'].create({
            'company_id': self.env.company.id,
            'name': 'Partner 2',
            'company_type': 'company',
            'country_id': self.env.ref("base.in").id,
            'state_id': self.env.ref("base.state_in_mh").id,
        })

        test_partner_3 = self.env['res.partner'].create({
            'name': 'Partner 3',
            'company_type': 'person',
            'parent_id': test_partner_1.id,
            'is_company': False,
            'customer_rank': 1,
            'country_id': self.env.ref("base.in").id,
            'state_id': self.env.ref("base.state_in_dl").id,
        })

        # ==== Invoices ====
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': test_partner_1.id,
            'partner_shipping_id': test_partner_2.id,
            'country_code': 'IN',
        })

        self.assertNotEqual(invoice.partner_id.commercial_partner_id, invoice.partner_shipping_id.commercial_partner_id)
        self.assertEqual(invoice.l10n_in_state_id, invoice.partner_id.state_id)

        invoice.write({
            'partner_shipping_id': test_partner_3.id,
        })

        self.assertEqual(invoice.partner_id.commercial_partner_id, invoice.partner_shipping_id.commercial_partner_id)
        self.assertEqual(invoice.l10n_in_state_id, invoice.partner_shipping_id.state_id)

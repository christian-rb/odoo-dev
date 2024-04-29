from odoo import Command, fields
from odoo.tests import tagged
from odoo.tests.common import Form
from .common import PurchaseTestCommon


@tagged('post_install', '-at_install')
class TestPurchaseOrderProcess(PurchaseTestCommon):

    def test_00_cancel_purchase_order_flow(self):
        """ Test cancel purchase order with group user."""

        # In order to test the cancel flow,start it from canceling confirmed purchase order.
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.env['res.partner'].create({'name': 'My Partner'}).id,
            'state': 'draft',
        })
        po_edit_with_user = purchase_order.with_user(self.res_users_purchase_user)

        # Confirm the purchase order.
        po_edit_with_user.button_confirm()

        # Check the "Approved" status  after confirmed RFQ.
        self.assertEqual(po_edit_with_user.state, 'purchase', 'Purchase: PO state should be "Purchase')

        # First cancel receptions related to this order if order shipped.
        po_edit_with_user.picking_ids.action_cancel()

        # Able to cancel purchase order.
        po_edit_with_user.button_cancel()

        # Check that order is cancelled.
        self.assertEqual(po_edit_with_user.state, 'cancel', 'Purchase: PO state should be "Cancel')

    def test_01_packaging_propagation(self):
        """Create a PO with lines using packaging, check the packaging propagate
        to its move.
        """
        product = self.env['product.product'].create({
            'name': 'Product with packaging',
            'type': 'product',
        })

        packaging = self.env['product.packaging'].create({
            'name': 'box',
            'product_id': product.id,
        })

        po = self.env['purchase.order'].create({
            'partner_id': self.env['res.partner'].create({'name': 'My Partner'}).id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'product_qty': 1.0,
                    'product_uom': product.uom_id.id,
                    'product_packaging_id': packaging.id,
                })],
        })
        po.button_confirm()
        self.assertEqual(po.order_line.move_ids.product_packaging_id, packaging)

    def test_purchase_batching(self):
        """
        With autobatch receipts, check that you can create backorders for
        pickings related to the batch.
        """
        warehouse = self.warehouse_1
        warehouse.in_type_id.auto_batch = True
        warehouse.in_type_id.batch_group_by_partner = True
        product_1, product_2 = self.product_1, self.product_2
        po_1 = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': product_1.id,
                    'product_qty': 1.0,
                    'product_uom': product_1.uom_id.id,
                })],
            'picking_type_id':  warehouse.in_type_id.id,
        })
        po_1.button_confirm()
        po_2 = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': product_1.id,
                    'product_qty': 1.0,
                    'product_uom': product_1.uom_id.id,
                }),
                Command.create({
                    'product_id': product_2.id,
                    'product_qty': 1.0,
                    'product_uom': product_2.uom_id.id,
                }),
            ],
            'picking_type_id':  warehouse.in_type_id.id,
        })
        po_2.button_confirm()
        picking_1, picking_2 = po_1.picking_ids, po_2.picking_ids
        batch = picking_1.batch_id
        self.assertEqual(batch.picking_ids, picking_1 | picking_2)
        picking_2.move_ids.filtered(lambda m: m.product_id == product_1).quantity = 0.0
        backorder_wizard_dict = picking_2.button_validate()
        backorder_wizard = Form(self.env[backorder_wizard_dict['res_model']].with_context(backorder_wizard_dict['context'])).save()
        backorder_wizard.process()
        self.assertTrue(picking_2.state, 'done')
        self.assertFalse(picking_2 in batch.picking_ids)
        self.assertEqual(batch.picking_ids, picking_1 | po_2.picking_ids.filtered(lambda p: p.state != 'done'))

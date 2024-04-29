# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import Form, tagged
from odoo.addons.mrp.tests.common import TestMrpCommon
from odoo.exceptions import AccessError


@tagged('post_install', '-at_install')
class TestMrpRepairFlows(TestMrpCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.ref('base.group_user').write({'implied_ids': [(4, cls.env.ref('stock.group_production_lot').id)]})

    def test_possible_to_add_kit_after_confirm(self):
        """
        Test that it is possible to add a kit manufactured product to an already confirmed Repair Order
        """
        repaired = self.env['product.product'].create({'name': 'Repaired'})
        part = self.env['product.product'].create({'name': 'Kit Component'})
        kit = self.env['product.product'].create({
            'name': 'Kit',
            'type': 'product',
        })
        bom = self.env['mrp.bom'].create({
            'product_id': kit.id,
            'product_tmpl_id': kit.product_tmpl_id.id,
            'type': 'phantom',
        })
        bom.write({
            'bom_line_ids': [self.env['mrp.bom.line'].create({
                'product_id': part.id,
                'product_tmpl_id': part.product_tmpl_id.id,
                'bom_id': bom.id,
            }).id],
        })
        try:
            # create repair order and confirm it
            ro_form = Form(self.env['repair.order'])
            ro_form.product_id = repaired
            ro = ro_form.save()
            ro.action_validate()
            # add kit
            with ro_form.move_ids.new() as ro_line:
                ro_line.repair_line_type = 'add'
                ro_line.product_id = kit
            ro_form.save()
        except AccessError:
            self.fail("Cannot add kit manufactured product to existing repair order")

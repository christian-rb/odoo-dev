# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.tests import HttpCase, tagged


@tagged('-at_install', 'post_install')
class TestPurchaseOrderTour(HttpCase):

    def test_manual_price_unit_computation(self):
        """ Computation of the unit price if it is manually set and also change it with respect to vendor  """
        self.env['res.config.settings'].create({'group_uom': True}).execute()
        url = "/web"
        self.start_tour(url, 'purchase_order_vendor_conformation_tour', login='admin', timeout=60)

from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _get_edi_builders(self, edi_builders):
        edi_builders.append(self.env['purchase.edi.xml.ubl_bis3'])

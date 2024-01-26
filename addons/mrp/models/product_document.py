
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductDocument(models.Model):
    _inherit = 'product.document'

    def _default_attached_on_mrp(self):
        return "bom" if self.env.context.get('bom_id') else "hidden"

    attached_on_mrp = fields.Selection(
        selection=[
            ('hidden', "Hidden"),
            ('bom', "Bill of Materials")
        ],
        string="MRP : Visible at",
        help="Leave empty if document only accessible on product form.\n"
            "Select Bill of Materials to visualise this document as a product attachment when this product is in a bill of material.\n"
            "Select Manufacturing Order and the document will be visible in the chatter of the production order.",
        default=_default_attached_on_mrp,
    )

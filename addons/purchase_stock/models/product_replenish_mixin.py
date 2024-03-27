# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ProductReplenishMixin(models.AbstractModel):
    _inherit = 'product.replenish.mixin'

    supplier_id = fields.Many2one("product.supplierinfo", string="Vendor")
    show_vendor = fields.Boolean(compute="_compute_show_vendor")

    @api.depends('route_id')
    def _compute_show_vendor(self):
        for rec in self:
            rec.show_vendor = rec._get_show_vendor(rec.route_id)

    def _get_show_vendor(self, route):
        return route == self.env.ref('purchase_stock.route_warehouse0_buy', raise_if_not_found=False)

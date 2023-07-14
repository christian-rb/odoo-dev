from odoo import models, fields


class StockPickingBatchWarning(models.TransientModel):
    _name = 'stock.picking.batch.warning'
    _description = 'If any picking line has 0 qty done then this wizard will warn before removing the picking line'

    picking_ids = fields.Many2many('stock.picking')

    def confirm_batch(self):
        context = self.env.context.get('context')
        return self.picking_ids.with_context(skip_immediate=True, **context).button_validate()

from odoo import _, models
from odoo.exceptions import UserError


class ProductTemplateImportCSV(models.TransientModel):

    _inherit = 'base_import.import'

    def execute_import(self, fields, columns, options, dryrun=False):
        res = super().execute_import(fields, columns, options, dryrun=dryrun)
        if options.get('product_import'):
            location = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1).lot_stock_id.id
            templates = self.env['product.template'].browse(res.get('ids'))
            for template in templates:
                if template.tracking == 'lot':
                    if not template.lot_id:
                        raise UserError(_('Please enter the lot number'))
                    lot_id = self.env['stock.lot'].create({'product_id': template.product_variant_id.id, 'name': template.lot_id})
                elif template.tracking == 'serial':
                    if not template.lot_id:
                        raise UserError(_('Please enter the serial number'))
                    if template.available_quantity != 1.0:
                        raise UserError(_('Product with serial number must have quantity 1'))
                    lot_id = self.env['stock.lot'].create({'product_id': template.product_variant_id.id, 'name': template.lot_id})
                elif template.lot_id and template.tracking not in ('lot', 'serial'):
                    raise UserError(_('Please set tracking field to lot id/SN'))
                if template.product_variant_id.exists():
                    vals = {
                        'product_id': template.product_variant_id.id,
                        'location_id': location,
                        'inventory_quantity': template.available_quantity,
                    }
                    if template.lot_id:
                        vals.update({'lot_id': lot_id.id})
                    self.env['stock.quant'].with_context(inventory_mode=True).create(vals).action_apply_inventory()
        return res

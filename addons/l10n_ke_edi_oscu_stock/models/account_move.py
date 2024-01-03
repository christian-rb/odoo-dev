# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, Command, fields, models
from odoo.exceptions import UserError



class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends(
        'invoice_line_ids.purchase_line_id',
        'invoice_line_ids.purchase_line_id.qty_received',
        'invoice_line_ids.sale_line_ids.qty_delivered',
        'move_type'
    )
    def _compute_l10n_ke_validation_message(self):
        super()._compute_l10n_ke_validation_message()
        for move in self.filtered(lambda m: any(l.product_id.type == 'product' for l in m.invoice_line_ids)):
            # Search related purchases/sales to see if the amounts correspond
            purchase_lines_to_check = move.invoice_line_ids.mapped('purchase_line_id')
            if not purchase_lines_to_check and move.is_purchase_document() or any(
                    pl.qty_received != pl.qty_invoiced and pl.product_id.type == 'product' for pl in purchase_lines_to_check):
                message = move.l10n_ke_validation_message or {}
                message.update(
                    {'waiting_receipt': {'message': _('Received quantities and vendor bill do not correspond'),
                                         'blocking': True}})
                move.l10n_ke_validation_message = message
            sale_lines_to_check = move.invoice_line_ids.mapped('sale_line_ids')
            if not sale_lines_to_check and move.is_sale_document() or any(
                    sl.qty_delivered != sl.qty_invoiced and sl.product_id.type == 'product' for sl in sale_lines_to_check):
                message = move.l10n_ke_validation_message or {}
                message.update(
                    {'waiting_picking': {'message': _('Sent quantities and customer invoice do not correspond'),
                                         'blocking': True}})
                move.l10n_ke_validation_message = message

    def action_l10n_ke_oscu_confirm_vendor_bill(self):
        super().action_l10n_ke_oscu_confirm_vendor_bill()
        if any(move.l10n_ke_oscu_invoice_number for move in self):
            # Trigger cron
            self.env.ref("l10n_ke_edi_oscu_stock.ir_cron_send_stock_moves")._trigger()

    def action_l10n_ke_create_purchase_order(self):
        self.ensure_one()
        if self.invoice_line_ids.mapped('purchase_line_id'):
            raise UserError(_("You have got a purchase order linked already.  "))
        lines = self.invoice_line_ids
        vals = []
        for line in lines:
            if line.display_type == 'product' and not line.product_id:
                raise UserError(_("Please make sure that all the lines have products and uoms. "))
            vals.append(Command.create({
                'product_id': line.product_id.id,
                'product_qty': line.quantity,
                'product_uom': line.product_uom_id.id,
                'price_unit': line.price_unit,
                'invoice_lines': line.ids,
                'date_planned': fields.Date.context_today(self),
                'taxes_id': line.tax_ids.ids,
                'display_type': line.display_type if line.display_type in ['line_section', 'line_note'] else False,
            }))

        po = self.env['purchase.order'].create({
            'partner_id': self.partner_id.id,
            'order_line': vals,
            'company_id': self.company_id.id,
        })
        action = {
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_id': po.id,
        }
        return action

    def action_l10n_ke_create_sale_order(self):
        self.ensure_one()
        if self.invoice_line_ids.mapped('sale_line_ids'):
            raise UserError(_("You have got a sale order linked already.  "))
        lines = self.invoice_line_ids
        vals = []
        for line in lines:
            if line.display_type == 'product' and not line.product_id:
                raise UserError(_("Please make sure that all the lines have products and uoms. "))
            vals.append(Command.create({
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'product_uom': line.product_uom_id.id,
                'price_unit': line.price_unit,
                'invoice_lines': line.ids,
                'tax_id': line.tax_ids.ids,
                'display_type': line.display_type if line.display_type in ['line_section', 'line_note'] else False,
            }))

        so = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'order_line': vals,
            'company_id': self.company_id.id,
        })
        action = {
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_id': so.id,
        }
        return action

    def _l10n_ke_oscu_send_customer_invoice(self):
        content, error = super()._l10n_ke_oscu_send_customer_invoice()
        if not error:
            self.env.ref("l10n_ke_edi_oscu_stock.ir_cron_send_stock_moves")._trigger()
        return content, error


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    product_id = fields.Many2one(compute='_compute_product_id', store=True, readonly=False, precompute=True)

    @api.depends('purchase_line_id')
    def _compute_product_id(self):
        for line in self.filtered(lambda l: not l.product_id and l.purchase_line_id.product_id):
            line.product_id = line.purchase_line_id.product_id.id
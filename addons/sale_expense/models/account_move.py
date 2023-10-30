# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    expense_sheet_id = fields.One2many(
        comodel_name='hr.expense.sheet',
        inverse_name='account_move_id',
        string='Expense Sheet',
        readonly=True
    )

    def _reverse_moves(self, default_values_list=None, cancel=False):
        expensed_sols = self.mapped('expense_sheet_id')._get_sale_order_lines()
        if expensed_sols:
            expensed_sols.write({'qty_delivered': 0., 'product_uom_qty': 0.})
        return super()._reverse_moves(default_values_list, cancel)

    def button_draft(self):
        res = super().button_draft()
        expensed_sols = self.mapped('expense_sheet_id')._get_sale_order_lines()
        if expensed_sols:
            expensed_sols.write({'qty_delivered': 0., 'product_uom_qty': 0.})
        return res

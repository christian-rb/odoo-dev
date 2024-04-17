# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.tools import format_date


class AccountOrderLine(models.AbstractModel):
    # This class enables down payment support for child records of account.order that can be down payments
    _name = 'account.order.line'
    _description = 'Account Order Line'

    is_downpayment = fields.Boolean(string="Is a down payment",
                                    help="Down payments are made when creating account moves from an order."
                                         " They are not copied when duplicating an order.")

    # To override
    invoice_lines = fields.One2many('account.move.line')
    display_type = fields.Selection(
        [('line_section', "Section"), ('line_note', "Note")],
        default=False,
        help="Technical field for UX purpose.")
    product_id = fields.Many2one('product.product')
    name = fields.Text(compute='_compute_name')
    order_id = fields.Many2one('account.order')
    qty_to_invoice = fields.Float()
    price_unit = fields.Float()
    tax_ids = fields.Many2many('account.tax')
    product_uom = fields.Many2one('uom.uom')
    discount = fields.Float()


    def _has_valid_qty_to_invoice(self, final=False):
        """
        Returns whether this account order line has a valid quantity for creating an invoice line from it.
        Used in account order to decide whether to create an invoice line for this entry.
        """
        raise NotImplementedError  # To override

    def _prepare_invoice_line(self, move=False, **optional_values):
        """
        Returns a dictionary of values to be used for creating the invoice line from this account order line.
        Used in account order to create the invoice lines.
        """
        self.ensure_one()
        return {
            'display_type': self.display_type or 'product',
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'discount': self.discount,
            'is_downpayment': self.is_downpayment,
        }

    def _get_invoice_lines(self):
        self.ensure_one()
        if self._context.get('accrual_entry_date'):
            return self.invoice_lines.filtered(
                lambda l: l.move_id.invoice_date and l.move_id.invoice_date <= self._context['accrual_entry_date']
            )
        else:
            return self.invoice_lines

    def _get_downpayment_state(self):
        self.ensure_one()

        if self.display_type:
            return None

        invoice_lines = self._get_invoice_lines()
        if all(line.parent_state == 'draft' for line in invoice_lines):
            return 'draft'
        if all(line.parent_state == 'cancel' for line in invoice_lines):
            return 'cancel'

        return None

    def _compute_name(self):
        for line in self:
            if line.is_downpayment:
                lang = line.order_id._get_lang()
                if lang != self.env.lang:
                    line = line.with_context(lang=lang)

                line.name = line._get_downpayment_description()

    def _get_downpayment_description(self):
        self.ensure_one()
        if self.display_type:
            return _("Down Payments")

        dp_state = self._get_downpayment_state()
        name = _("Down Payment")
        if dp_state == 'draft':
            name = _(
                "Down Payment: %(date)s (Draft)",
                date=format_date(self.env, self.create_date.date()),
            )
        elif dp_state == 'cancel':
            name = _("Down Payment (Cancelled)")
        else:
            invoice = self._get_invoice_lines().move_id
            if len(invoice) == 1 and invoice.payment_reference and invoice.invoice_date:
                name = _(
                    "Down Payment (ref: %(reference)s on %(date)s)",
                    reference=invoice.payment_reference,
                    date=format_date(self.env, invoice.invoice_date),
                )

        return name

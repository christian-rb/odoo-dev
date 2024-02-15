# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountPaymentMethodLine(models.Model):
    _inherit = 'account.payment.method.line'

    l10n_gr_edi_payment_method_id = fields.Selection(
        selection=[
            ('1', '1 - Domestic Payments Account Number'),
            ('2', '2 - Foreign Payments Account Number'),
            ('3', '3 - Cash'),
            ('4', '4 - Check'),
            ('5', '5 - On credit'),
            ('6', '6 - Web Banking'),
            ('7', '7 - POS / e-POS'),
        ],
        string='MyDATA Payment Method',
        help='Specify the payment method classification required for sending invoice payment data to MyDATA')

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
<<<<<<< HEAD:addons/account_payment/models/account_payment_method.py
        for code, _desc in self.env['payment.provider']._fields['code'].selection:
            if code in ('none', 'custom'):
                continue
            res[code] = {
                'mode': 'unique',
                'domain': [('type', '=', 'bank')],
            }
||||||| parent of bb65934e42fb (temp):addons/payment_mollie/models/account_payment_method.py
        res['mollie'] = {'mode': 'unique', 'domain': [('type', '=', 'bank')]}
=======
        res['mollie'] = {'mode': 'electronic', 'domain': [('type', '=', 'bank')]}
>>>>>>> bb65934e42fb (temp):addons/payment_mollie/models/account_payment_method.py
        return res

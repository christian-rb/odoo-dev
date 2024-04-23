# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_pos_payment_method(self):
        result = super()._loader_params_pos_payment_method()
        result['search_params']['fields'].append('viva_wallet_terminal_id')
        return result

    def _load_data_params(self, config_id):
        params = super()._load_data_params(config_id)
        params['pos.payment.method']['fields'].append('viva_wallet_bearer_token')
        return params

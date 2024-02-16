# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression


class AccountPaymentMethodLine(models.Model):
    _inherit = "account.payment.method.line"

<<<<<<< HEAD:addons/account_payment/models/account_payment_method_line.py
    payment_provider_id = fields.Many2one(
        comodel_name='payment.provider',
        compute='_compute_payment_provider_id',
        store=True
||||||| parent of bb65934e42fb (temp):addons/payment/models/account_payment_method.py
    payment_acquirer_id = fields.Many2one(
        comodel_name='payment.acquirer',
        compute='_compute_payment_acquirer_id',
        store=True
=======
    payment_acquirer_id = fields.Many2one(
        comodel_name='payment.acquirer',
        compute='_compute_payment_acquirer_id',
        store=True,
        readonly=False,
        domain="[('provider', '=', code)]",
>>>>>>> bb65934e42fb (temp):addons/payment/models/account_payment_method.py
    )
    payment_provider_state = fields.Selection(
        related='payment_provider_id.state'
    )

    @api.depends('payment_method_id')
<<<<<<< HEAD:addons/account_payment/models/account_payment_method_line.py
    def _compute_payment_provider_id(self):
        providers = self.env['payment.provider'].sudo().search([
            ('code', 'in', self.mapped('code')),
            ('company_id', 'in', self.journal_id.company_id.ids),
        ])

        # Make sure to pick the active provider, if any.
        providers_map = dict()
        for provider in providers:
            current_value = providers_map.get((provider.code, provider.company_id), False)
            if current_value and current_value.state != 'disabled':
                continue

            providers_map[(provider.code, provider.company_id)] = provider
||||||| parent of bb65934e42fb (temp):addons/payment/models/account_payment_method.py
    def _compute_payment_acquirer_id(self):
        acquirers = self.env['payment.acquirer'].sudo().search([
            ('provider', 'in', self.mapped('code')),
            ('company_id', 'in', self.journal_id.company_id.ids),
        ])

        # Make sure to pick the active acquirer, if any.
        acquirers_map = dict()
        for acquirer in acquirers:
            current_value = acquirers_map.get((acquirer.provider, acquirer.company_id), False)
            if current_value and current_value.state != 'disabled':
                continue

            acquirers_map[(acquirer.provider, acquirer.company_id)] = acquirer
=======
    def _compute_payment_acquirer_id(self):
        results = self.journal_id._get_journals_payment_method_information()
        manage_acquirers = results['manage_acquirers']
        method_information_mapping = results['method_information_mapping']
        acquirers_per_code = results['acquirers_per_code']
>>>>>>> bb65934e42fb (temp):addons/payment/models/account_payment_method.py

        for line in self:
<<<<<<< HEAD:addons/account_payment/models/account_payment_method_line.py
            code = line.payment_method_id.code
            company = line.journal_id.company_id
            line.payment_provider_id = providers_map.get((code, company), False)
||||||| parent of bb65934e42fb (temp):addons/payment/models/account_payment_method.py
            code = line.payment_method_id.code
            company = line.journal_id.company_id
            line.payment_acquirer_id = acquirers_map.get((code, company), False)
=======
            journal = line.journal_id
            company = journal.company_id
            if (
                company
                and line.payment_method_id
                and manage_acquirers
                and method_information_mapping[line.payment_method_id.id]['mode'] == 'electronic'
            ):
                acquirer_ids = acquirers_per_code.get(company.id, {}).get(line.code, set())

                # Exclude the 'unique' / 'electronic' values that are already set on the journal.
                protected_acquirer_ids = set()
                for payment_type in ('inbound', 'outbound'):
                    lines = journal[f'{payment_type}_payment_method_line_ids']
                    for journal_line in lines:
                        if journal_line.payment_method_id:
                            if manage_acquirers and method_information_mapping[journal_line.payment_method_id.id]['mode'] == 'electronic':
                                protected_acquirer_ids.add(journal_line.payment_acquirer_id.id)

                candidates_acquirer_ids = acquirer_ids - protected_acquirer_ids
                if candidates_acquirer_ids:
                    line.payment_acquirer_id = list(candidates_acquirer_ids)[0]
>>>>>>> bb65934e42fb (temp):addons/payment/models/account_payment_method.py

    @api.model
    def _get_payment_method_domain(self, code):
        # OVERRIDE
        domain = super()._get_payment_method_domain(code)
        information = self._get_payment_method_information().get(code)

        unique = information.get('mode') == 'unique'
        if unique:
            company_ids = self.env['payment.provider'].sudo().search([('code', '=', code)]).mapped('company_id')
            if company_ids:
                domain = expression.AND([domain, [('company_id', 'in', company_ids.ids)]])

        return domain

    @api.ondelete(at_uninstall=False)
    def _unlink_except_active_provider(self):
        """ Ensure we don't remove an account.payment.method.line that is linked to a provider
        in the test or enabled state.
        """
        active_provider = self.payment_provider_id.filtered(lambda provider: provider.state in ['enabled', 'test'])
        if active_provider:
            raise UserError(_(
                "You can't delete a payment method that is linked to a provider in the enabled "
                "or test state.\n""Linked providers(s): %s",
                ', '.join(a.display_name for a in active_provider),
            ))

    def action_open_provider_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Provider'),
            'view_mode': 'form',
            'res_model': 'payment.provider',
            'target': 'current',
            'res_id': self.payment_provider_id.id
        }

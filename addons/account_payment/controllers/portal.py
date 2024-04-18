# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.account.controllers import portal
from odoo.addons.payment.controllers.portal import PaymentPortal


class PortalAccount(portal.PortalAccount, PaymentPortal):

    @http.route(['/my/invoices/overdue'], type='http', auth="public", methods=['GET'], website=True)
    def portal_my_overdue_invoices(self, access_token=None, **kw):
        overdue_invoices = None
        if access_token:
            partner = request.env['account.move'].sudo().search([('access_token', '=', access_token)]).partner_id
            overdue_invoices = request.env['account.move'].sudo().search(self._get_overdue_invoices_domain() + [('partner_id', '=', partner.id)])
        else:
            try:
                request.env['account.move'].check_access_rights('read')
                overdue_invoices = request.env['account.move'].search(self._get_overdue_invoices_domain())
            except (AccessError, MissingError):
                return request.redirect('/my')

        values = self._overdue_invoices_get_page_view_values(overdue_invoices, access_token, **kw)
        if access_token and 'post_params' in values:
            # sudo_payment signals that invoices tokens needn't be validated
            values['post_params']['sudo_payment'] = True
        return request.render("account_payment.portal_overdue_invoices_page", values)

    def _overdue_invoices_get_page_view_values(self, overdue_invoices, access_token, **kwargs):
        values = {'page_name': 'overdue_invoices'}

        if len(overdue_invoices) == 0:
            return values

        batch = overdue_invoices.mapped('line_ids')
        total_amount = sum(overdue_invoices.mapped('amount_total'))
        residual_amount = sum(overdue_invoices.mapped('amount_residual'))
        payment_date = fields.Date.today()
        batch_name = request.env['account.payment.register'].get_next_batch_communication(date=payment_date, batch=batch)
        payment = {
            'date': payment_date,
            'reference': batch_name,
            'amount': total_amount,
            'currency': overdue_invoices[0].company_currency_id,
        }

        values |= {'payment': payment}

        # There is an assumption that all invoices have the same partner, company, and currency
        # It is also assumed that they all have the same access rights
        first_invoice = overdue_invoices[0]
        partner_id = first_invoice.partner_id
        company_id = first_invoice.company_id
        currency_id = first_invoice.currency_id
        access_token = access_token or first_invoice._portal_ensure_token()

        common_view_values = self._get_common_page_view_values(
            invoices_data={
                'partner_id': partner_id,
                'company_id': company_id,
                'total_amount': total_amount,
                'currency_id': currency_id,
                'residual_amount': residual_amount,
                'invoice_ids': overdue_invoices.mapped('id'),
                'payment_reference': batch_name,
                'landing_route': '/my/invoices/',
            },
            access_token=access_token,
            **kwargs)
        values |= common_view_values
        return values

    def _invoice_get_page_view_values(self, invoice, access_token, **kwargs):
        values = super()._invoice_get_page_view_values(invoice, access_token, **kwargs)

        if not invoice._has_to_be_paid():
            # Do not compute payment-related stuff if given invoice doesn't have to be paid.
            return values

        common_view_values = self._get_common_page_view_values(
            invoices_data={
                'partner_id': invoice.partner_id,
                'company_id': invoice.company_id,
                'total_amount': invoice.amount_total,
                'currency_id': invoice.currency_id,
                'residual_amount': invoice.amount_residual,
                'invoice_ids': [invoice.id],
                'landing_route': invoice.get_portal_url(),
            },
            access_token=access_token,
            **kwargs)
        values |= common_view_values
        return values

    def _get_common_page_view_values(self, invoices_data, access_token, **kwargs):
        logged_in = not request.env.user._is_public()
        # We set partner_id to the partner id of the current user if logged in, otherwise we set it
        # to the invoice partner id. We do this to ensure that payment tokens are assigned to the
        # correct partner and to avoid linking tokens to the public user.
        partner_sudo = request.env.user.partner_id if logged_in else invoices_data['partner_id']
        invoice_company = invoices_data['company_id'] or request.env.company

        availability_report = {}
        # Select all the payment methods and tokens that match the payment context.
        providers_sudo = request.env['payment.provider'].sudo()._get_compatible_providers(
            invoice_company.id,
            partner_sudo.id,
            invoices_data['total_amount'],
            currency_id=invoices_data['currency_id'].id,
            report=availability_report,
        )  # In sudo mode to read the fields of providers and partner (if logged out).
        payment_methods_sudo = request.env['payment.method'].sudo()._get_compatible_payment_methods(
            providers_sudo.ids,
            partner_sudo.id,
            currency_id=invoices_data['currency_id'].id,
            report=availability_report,
        )  # In sudo mode to read the fields of providers.
        tokens_sudo = request.env['payment.token'].sudo()._get_available_tokens(
            providers_sudo.ids,
            partner_sudo.id,
        )  # In sudo mode to read the partner's tokens (if logged out) and provider fields.

        # Make sure that the partner's company matches the invoice's company.
        company_mismatch = not PaymentPortal._can_partner_pay_in_company(
            partner_sudo,
            invoice_company,
        )

        portal_page_values = {
            'company_mismatch': company_mismatch,
            'expected_company': invoice_company,
        }
        payment_form_values = {
            'show_tokenize_input_mapping': PaymentPortal._compute_show_tokenize_input_mapping(
                providers_sudo
            ),
        }

        post_params = {'invoice_ids': invoices_data['invoice_ids']}
        if 'payment_reference' in invoices_data:
            post_params['payment_reference'] = invoices_data['payment_reference']

        payment_context = {
            'amount': invoices_data['residual_amount'],
            'currency': invoices_data['currency_id'],
            'partner_id': partner_sudo.id,
            'providers_sudo': providers_sudo,
            'payment_methods_sudo': payment_methods_sudo,
            'tokens_sudo': tokens_sudo,
            'availability_report': availability_report,
            'transaction_route': '/invoice/transaction/',
            'post_params': post_params,
            'landing_route': invoices_data['landing_route'],
            'access_token': access_token,
        }

        return portal_page_values | payment_form_values | payment_context | self._get_extra_payment_form_values(**kwargs)

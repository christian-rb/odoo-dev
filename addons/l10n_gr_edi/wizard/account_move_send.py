# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models


class AccountMoveSend(models.TransientModel):
    _inherit = 'account.move.send'

    l10n_gr_mydata_enable = fields.Boolean(compute='_compute_l10n_gr_mydata_enable')
    l10n_gr_mydata_checkbox = fields.Boolean(
        string="Send to MyDATA",
        compute='_compute_l10n_gr_mydata_checkbox',
        store=True,
        readonly=False,
    )

    def _get_wizard_values(self):
        # EXTENDS 'account'
        values = super()._get_wizard_values()
        values['l10n_gr_mydata'] = self.l10n_gr_mydata_checkbox
        return values

    @api.depends('move_ids')
    def _compute_l10n_gr_mydata_enable(self):
        for wizard in self:
            wizard.l10n_gr_mydata_enable = wizard.company_id.country_code == 'GR' and \
                                           any(move.l10n_gr_edi_state != 'sent' for move in wizard.move_ids)

    @api.depends('l10n_gr_mydata_enable')
    def _compute_l10n_gr_mydata_checkbox(self):
        for wizard in self:
            wizard.l10n_gr_mydata_checkbox = wizard.l10n_gr_mydata_enable

    @api.model
    def _call_web_service_before_invoice_pdf_render(self, invoices_data):
        # EXTENDS 'account'
        super()._call_web_service_before_invoice_pdf_render(invoices_data)
        invoices = self.env['account.move']

        # Create invoice batches
        for invoice, invoice_data in invoices_data.items():
            if invoice_data.get('l10n_gr_mydata') and invoice.l10n_gr_edi_state != 'sent':
                if errors := invoice.mydata_prepare_constraints():
                    invoice_data['error'] = {
                        'error_title': _("Error when preparing invoice XML to be sent to MyDATA"),
                        'errors': errors,
                    }
                else:
                    invoices |= invoice

        # Send invoice batches
        if invoices:
            invoices.mydata_send_invoices()

        # Handle errors post send process
        for invoice, invoice_data in invoices_data.items():
            if invoice in invoices and invoice.l10n_gr_edi_state == 'error':
                invoice_data['error'] = {
                    'error_title': _("Error when sending invoice XML to MyDATA"),
                    'errors': invoice.l10n_gr_edi_message.split('\n'),
                }

        if self._can_commit():
            self._cr.commit()

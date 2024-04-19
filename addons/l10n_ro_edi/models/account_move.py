# Part of Odoo. See LICENSE file for full copyright and licensing details.
import requests

from odoo import models, fields, _, api
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_ro_edi_state = fields.Selection(related='l10n_ro_edi_active_document_id.state', store=True)
    l10n_ro_edi_message = fields.Char(related='l10n_ro_edi_active_document_id.message')
    l10n_ro_edi_document_ids = fields.One2many(
        comodel_name='ciusro.document',
        inverse_name='move_id')
    l10n_ro_edi_active_document_id = fields.Many2one('ciusro.document')

    @api.depends('l10n_ro_edi_state')
    def _compute_show_reset_to_draft_button(self):
        """ Prevent user to reset move to draft when there's an
        active sending document or an OK response has been received """
        super()._compute_show_reset_to_draft_button()
        for move in self:
            if move.l10n_ro_edi_state in ('sending', 'ok', 'sent'):
                move.show_reset_to_draft_button = False

    def _l10n_ro_edi_prepare_values(self, xml_data):
        errors = []
        if not self.company_id.l10n_ro_edi_access_token:
            errors.append(_('Romanian access token not found. Please generate or fill it in the settings.'))
        if not xml_data:
            errors.append(_('CIUS-RO XML attachment not found.'))
        return errors

    def _l10n_ro_edi_fetch_batch_status(self):
        documents = self.l10n_ro_edi_active_document_id.filtered(lambda d: d.state == 'sending')
        if not documents:
            raise UserError(_('The are no selected move in sending state'))

        session = requests.session()
        for document in documents:
            document._request_ciusro_fetch_status(session=session)

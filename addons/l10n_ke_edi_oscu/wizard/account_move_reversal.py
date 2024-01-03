# -*- coding: utf-8 -*-

from odoo import _, api, models, fields
from odoo.exceptions import UserError


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    l10n_ke_reason_code_id = fields.Many2one(
        comodel_name='l10n_ke_edi_oscu.code',
        domain="[('code_type', '=', '32')]",
        string="KRA Reason",
        help="Kenyan code for Credit Notes")
    l10n_ke_validation_message = fields.Json(compute='_compute_l10n_ke_validation_message')

    @api.depends('l10n_ke_reason_code_id')
    def _compute_l10n_ke_validation_message(self):
        for wizard in self:
            wizard.l10n_ke_validation_message = {
                'no_reason_code_warning': {
                    'message': _("A reason code is required when creating credit notes."),
                    'blocking': True,
                }
            } if wizard.country_code == 'KE' and not wizard.l10n_ke_reason_code_id else {}

    def _prepare_default_reversal(self, move):
        return {
            'l10n_ke_reason_code_id': self.l10n_ke_reason_code_id.id,
            **super()._prepare_default_reversal(move),
        }

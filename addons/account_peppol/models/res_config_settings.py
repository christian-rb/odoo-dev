# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models, modules
from odoo.exceptions import UserError, ValidationError

from odoo.addons.account_peppol.tools.demo_utils import handle_demo


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    account_peppol_edi_user = fields.Many2one(
        comodel_name='account_edi_proxy_client.user',
        string='EDI user',
        compute='_compute_account_peppol_edi_user',
    )
    account_peppol_contact_email = fields.Char(related='company_id.account_peppol_contact_email', readonly=False)
    account_peppol_eas = fields.Selection(related='company_id.peppol_eas', readonly=False)
    account_peppol_edi_identification = fields.Char(related='account_peppol_edi_user.edi_identification')
    account_peppol_endpoint = fields.Char(related='company_id.peppol_endpoint', readonly=False)
    account_peppol_migration_key = fields.Char(related='company_id.account_peppol_migration_key', readonly=False)
    account_peppol_proxy_state = fields.Selection(related='company_id.account_peppol_proxy_state', readonly=False)
    account_peppol_purchase_journal_id = fields.Many2one(related='company_id.peppol_purchase_journal_id', readonly=False)

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------

    @api.depends('is_account_peppol_eligible', 'account_peppol_edi_user')
    def _compute_account_peppol_mode_constraint(self):
        mode_constraint = self.env['ir.config_parameter'].sudo().get_param('account_peppol.mode_constraint')
        trial_param = self.env['ir.config_parameter'].sudo().get_param('saas_trial.confirm_token')
        self.account_peppol_mode_constraint = trial_param and 'demo' or mode_constraint or 'prod'

    @api.depends("company_id.account_edi_proxy_client_ids")
    def _compute_account_peppol_edi_user(self):
        for config in self:
            config.account_peppol_edi_user = config.company_id.account_edi_proxy_client_ids.filtered(
                lambda u: u.proxy_type == 'peppol')

    # -------------------------------------------------------------------------
    # BUSINESS ACTIONS
    # -------------------------------------------------------------------------

    def action_open_peppol_form(self):
        return self.env['peppol.registration'].with_company(self.company_id)._action_open_peppol_form(reopen=False)

    @handle_demo
    def button_update_peppol_user_data(self):
        """
        Action for the user to be able to update their contact details any time
        Calls /update_user on the iap server
        """
        self.ensure_one()

        if not self.account_peppol_contact_email or not self.account_peppol_phone_number:
            raise ValidationError(_("Contact email and phone number are required."))

        params = {
            'update_data': {
                'peppol_phone_number': self.account_peppol_phone_number,
                'peppol_contact_email': self.account_peppol_contact_email,
            }
        }

        self.account_peppol_edi_user._call_peppol_proxy(
            endpoint='/api/peppol/1/update_user',
            params=params,
        )

    @handle_demo
    def button_migrate_peppol_registration(self):
        """
        If the user is active, they need to request a migration key, generated on the IAP server.
        The migration key is then displayed in Peppol settings.
        Currently, reopening after migrating away is not supported.
        """
        self.ensure_one()

        if self.account_peppol_proxy_state != 'receiver':
            raise UserError(_("Can't migrate unless registered to receive documents."))

        response = self.account_peppol_edi_user._call_peppol_proxy(endpoint='/api/peppol/1/migrate_peppol_registration')
        self.account_peppol_migration_key = response['migration_key']

    @handle_demo
    def button_deregister_peppol_participant(self):
        """
        Deregister the edi user from Peppol network
        """
        self.ensure_one()

        if self.account_peppol_proxy_state == 'receiver':
            # fetch all documents and message statuses before unlinking the edi user
            # so that the invoices are acknowledged
            self.env['account_edi_proxy_client.user']._cron_peppol_get_message_status()
            self.env['account_edi_proxy_client.user']._cron_peppol_get_new_documents()
            if not modules.module.current_test:
                self.env.cr.commit()
            self.account_peppol_edi_user._call_peppol_proxy(endpoint='/api/peppol/1/cancel_peppol_registration')

        self.account_peppol_proxy_state = 'not_registered'
        if self.account_peppol_edi_user:
            self.account_peppol_edi_user.unlink()

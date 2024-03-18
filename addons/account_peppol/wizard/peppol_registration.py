# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models, modules
from odoo.exceptions import UserError, ValidationError

from odoo.addons.account_peppol.tools.demo_utils import handle_demo


class PeppolRegistration(models.TransientModel):
    _name = 'peppol.registration'
    _description = "Peppol Registration"

    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True,
        default=lambda self: self.env.company,
    )
    account_peppol_contact_email = fields.Char(related='company_id.account_peppol_contact_email', readonly=False)
    account_peppol_edi_mode = fields.Selection(
        selection=[('demo', 'Demo'), ('test', 'Test'), ('prod', 'Live')],
        compute='_compute_account_peppol_edi_mode',
        inverse='_inverse_account_peppol_edi_mode',
        readonly=False,
    )
    account_peppol_edi_user = fields.Many2one(
        comodel_name='account_edi_proxy_client.user',
        string='EDI user',
        compute='_compute_account_peppol_edi_user',
    )
    account_peppol_migration_key = fields.Char(related='company_id.account_peppol_migration_key', readonly=False)
    account_peppol_mode_constraint = fields.Selection(
        selection=[('demo', 'Demo'), ('test', 'Test'), ('prod', 'Live')],
        compute='_compute_account_peppol_mode_constraint',
        help="Using the config params, this field specifies which edi modes may be selected from the UI"
    )
    account_peppol_phone_number = fields.Char(related='company_id.account_peppol_phone_number', readonly=False)
    account_peppol_proxy_state = fields.Selection(related='company_id.account_peppol_proxy_state', readonly=False)
    account_peppol_verification_code = fields.Char(related='account_peppol_edi_user.peppol_verification_code', readonly=False)
    peppol_eas = fields.Selection(related='company_id.peppol_eas', readonly=False)
    peppol_endpoint = fields.Char(related='company_id.peppol_endpoint', readonly=False)
    peppol_warnings = fields.Json(
        string="Peppol warnings",
        compute="_compute_peppol_warnings",
    )
    smp_registration = fields.Boolean('Register as a receiver')

    # -------------------------------------------------------------------------
    # ONCHANGE METHODS
    # -------------------------------------------------------------------------

    @api.onchange('peppol_endpoint')
    def _onchange_peppol_endpoint(self):
        for wizard in self:
            if wizard.peppol_endpoint:
                wizard.peppol_endpoint = ''.join(char for char in wizard.peppol_endpoint if char.isalnum())

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------

    @api.depends("company_id.account_edi_proxy_client_ids")
    def _compute_account_peppol_edi_user(self):
        for wizard in self:
            wizard.account_peppol_edi_user = wizard.company_id.\
                account_edi_proxy_client_ids.filtered(lambda u: u.proxy_type == 'peppol')

    @api.depends('peppol_eas', 'peppol_endpoint')
    def _compute_peppol_warnings(self):
        for wizard in self:
            peppol_warnings = {}
            if (
                wizard.peppol_eas
                and wizard.peppol_endpoint
                and not wizard.company_id._check_peppol_endpoint_number(warning=True)
            ):
                peppol_warnings['company_peppol_endpoint_warning'] = {
                    'message': _("The endpoint number might not be correct. "
                                "Please check if you entered the right identification number."),
                }
            if wizard.company_id.country_code == 'BE' and wizard.peppol_eas not in (False, '0208'):
                peppol_warnings['company_peppol_eas_warning'] = {
                    'message': _("The recommended EAS code for Belgium is 0208. "
                                "The Endpoint should be the Company Registry number."),
                }
            wizard.peppol_warnings = peppol_warnings or False

    @api.depends('account_peppol_edi_user')
    def _compute_account_peppol_mode_constraint(self):
        mode_constraint = self.env['ir.config_parameter'].sudo().get_param('account_peppol.mode_constraint')
        trial_param = self.env['ir.config_parameter'].sudo().get_param('saas_trial.confirm_token')
        self.account_peppol_mode_constraint = trial_param and 'demo' or mode_constraint or 'prod'

    @api.depends('account_peppol_edi_user')
    def _compute_account_peppol_edi_mode(self):
        edi_mode = self.env['ir.config_parameter'].sudo().get_param('account_peppol.edi.mode')
        for wizard in self:
            if wizard.account_peppol_edi_user:
                wizard.account_peppol_edi_mode = wizard.account_peppol_edi_user.edi_mode
            else:
                wizard.account_peppol_edi_mode = edi_mode or 'prod'

    def _inverse_account_peppol_edi_mode(self):
        for wizard in self:
            if not wizard.account_peppol_edi_user and wizard.account_peppol_edi_mode:
                self.env['ir.config_parameter'].sudo().set_param('account_peppol.edi.mode', wizard.account_peppol_edi_mode)
                return

    # -------------------------------------------------------------------------
    # BUSINESS ACTIONS
    # -------------------------------------------------------------------------

    def _action_open_peppol_form(self, reopen=True):
        action_dict = {
            'name': _("Send via Peppol"),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'peppol.registration',
            'target': 'new',
        }

        if reopen:
            action_dict.update({
                'res_id': self.id,
                'context': {'disable_sms_verification': True},
            })
        return action_dict

    @handle_demo
    def button_peppol_sender_registration(self):
        """
        The first step of the Peppol onboarding.
        - Creates an EDI proxy user on the iap side, then the client side
        - Calls /activate_participant to mark the EDI user as peppol user
        - Allows the user to become a sender but not a receiver on the Peppol network.
        Basically, a Sender does not exist on the peppol network. They use our
        Access Point to send invoices to Peppol participants without having to register
        themselves.
        """
        self.ensure_one()

        if self.account_peppol_proxy_state != 'not_registered':
            raise UserError(
                _('Cannot register a user with a %s application', self.account_peppol_proxy_state))

        if not self.account_peppol_phone_number:
            raise ValidationError(_("Please enter a phone number to verify your application."))
        if not self.account_peppol_contact_email:
            raise ValidationError(_("Please enter a primary contact email to verify your application."))

        company = self.company_id
        edi_user = self.account_peppol_edi_user.sudo()._register_proxy_user(company, 'peppol', self.account_peppol_edi_mode)

        # if there is an error when activating the participant below,
        # the client side is rolled back and the edi user is deleted on the client side
        # but remains on the proxy side.
        # it is important to keep these two in sync, so commit before activating.
        if not modules.module.current_test:
            self.env.cr.commit()

        params = {
            'company_details': {
                'peppol_company_name': company.display_name,
                'peppol_company_vat': company.vat,
                'peppol_company_street': company.street,
                'peppol_company_city': company.city,
                'peppol_company_zip': company.zip,
                'peppol_country_code': company.country_id.code,
                'peppol_phone_number': self.account_peppol_phone_number,
                'peppol_contact_email': self.account_peppol_contact_email,
            },
        }

        edi_user._call_peppol_proxy(
            endpoint='/api/peppol/1/activate_participant',
            params=params,
        )

        self.button_send_peppol_verification_code()
        self.account_peppol_proxy_state = 'in_verification'
        return self._action_open_peppol_form()

    @handle_demo
    def button_peppol_smp_registration(self):
        """
        The second (optional) step in Peppol registration.
        The user can choose to become a Receiver and officially register on the Peppol
        network, i.e. receive documents from other Peppol participants.
        """
        self.ensure_one()

        if self.account_peppol_proxy_state != 'sender':
            raise UserError(
                _('Cannot register a user with a %s application', self.account_peppol_proxy_state))

        company = self.company_id
        edi_identification = self.account_peppol_edi_user._get_proxy_identification(company, 'peppol')

        if (
            company.partner_id._check_peppol_participant_exists(edi_identification)
            and not self.account_peppol_migration_key
        ):
            raise UserError(
                _("A participant with these details has already been registered on the network. "
                  "If you have previously registered to an alternative Peppol service, please deregister from that service, "
                  "or request a migration key before trying again."))

        self.account_peppol_edi_user._call_peppol_proxy(
            endpoint='/api/peppol/2/register_participant',
            params={
                'migration_key': self.account_peppol_migration_key,
            },
        )
        # once we sent the migration key over, we don't need it
        # but we need the field for future in case the user decided to migrate away from Odoo
        self.account_peppol_migration_key = False
        self.account_peppol_proxy_state = 'smp_registration'
        return self._action_open_peppol_form()

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
        return self._action_open_peppol_form()

    def button_send_peppol_verification_code(self):
        """
        Request user verification via SMS
        Calls the /send_verification_code to send the 6-digit verification code
        """
        self.ensure_one()

        # update contact details in case the user made changes
        self.button_update_peppol_user_data()

        self.account_peppol_edi_user._call_peppol_proxy(
            endpoint='/api/peppol/1/send_verification_code',
            params={'message': _("Your confirmation code is")},
        )
        self.account_peppol_proxy_state = 'in_verification'
        return self._action_open_peppol_form()

    def button_check_peppol_verification_code(self):
        """
        Calls /verify_phone_number to compare user's input and the
        code generated on the IAP server
        """
        self.ensure_one()

        if len(self.account_peppol_verification_code) != 6:
            raise ValidationError(_("The verification code should contain six digits."))

        self.account_peppol_edi_user._call_peppol_proxy(
            endpoint='/api/peppol/1/verify_phone_number',
            params={'verification_code': self.account_peppol_verification_code},
        )
        self.account_peppol_proxy_state = 'sender'
        self.account_peppol_verification_code = False
        if self.smp_registration:
            return self.button_peppol_smp_registration()
        return self._action_open_peppol_form()

    @handle_demo
    def button_deregister_peppol_participant(self):
        """
        Deregister the edi user from Peppol network
        """
        self.ensure_one()

        if self.account_peppol_proxy_state != 'receiver':
            self.account_peppol_proxy_state = 'not_registered'
            if self.account_peppol_edi_user:
                self.account_peppol_edi_user.unlink()

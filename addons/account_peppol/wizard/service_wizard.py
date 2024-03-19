# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from markupsafe import Markup

from odoo import api, Command, fields, models, _
from odoo.addons.account_edi_proxy_client.models.account_edi_proxy_user import AccountEdiProxyError

_logger = logging.getLogger(__name__)


class PeppolService(models.TransientModel):

    _name = 'account_peppol.service'
    _order = 'document_name'

    wizard_id = fields.Many2one('account_peppol.service.wizard')
    document_type_id = fields.Many2one('account_peppol.document_type')
    document_identifier = fields.Char()
    document_name = fields.Char()
    enabled = fields.Boolean(default=False)


class PeppolServiceConfig(models.TransientModel):

    _name = 'account_peppol.service.wizard'

    edi_user_id = fields.Many2one('account_edi_proxy_client.user', string='EDI user')
    service_json = fields.Json(help="JSON representation of peppol services as retrieved from the peppol server.")
    service_info = fields.Html(compute='_compute_service_info')
    service_ids = fields.One2many(
        comodel_name='account_peppol.service',
        inverse_name='wizard_id',
        readonly=False,
    )

    # -------------------------------------------------------------------------
    # COMPUTES
    # -------------------------------------------------------------------------

    def _compute_service_info(self):

        for wizard in self:
            message = ''
            if (non_configurable := [
                service for service in (wizard.service_json or {}).values()
                if service['configurable'] is False
            ]):
                message = Markup('%s<ul>%s</ul>') % (_(
                    "The following services are listed on your participant but cannot be configured here. "
                    "If you wish to configure them differently, please contact support."),
                    Markup().join(Markup('<li>%s</li>') % (service['document_name']) for service in non_configurable),
                )
            wizard.service_info = message


    # -------------------------------------------------------------------------
    # OVERRIDES
    # -------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        """Get the selectable document types.

        Synthesize a combination of locally available document types and those added to the user on
        the IAP, add the relevant services.
        """
        wizards = super().create(vals_list)
        supported_document_types = {
            identifier: {'document_name': name, 'enabled': False, 'configurable': True}
            for identifier, name
            in self.env['res.company']._peppol_get_supported_document_types().items()
        }
        for wizard in wizards:
            services = {**supported_document_types, **(wizard.service_json or {})}
            wizard.service_ids.create([{
                'document_identifier': identifier,
                'document_name': service['document_name'],
                'enabled': service['enabled'],
                'wizard_id': wizard.id,
            } for identifier, service  in services.items() if service['configurable']])
        return wizards

    def write(self, vals):
        """Interpret the write vals, and adapt them to make a request to update services."""
        res = super().write(vals)

        services = self.service_ids.read(['document_identifier', 'enabled'])
        updated_ids = [id for command, id, *args in vals.get('service_ids') if command == 1]
        to_create, to_update = {}, {}

        for service in services:
            if service['document_identifier'] not in self.service_json:
                to_create.update({service['document_identifier']: {'enabled': service['enabled']}})
                continue

            if service['id'] in updated_ids:
                to_update.update({service['document_identifier']: {'enabled': service['enabled']}})

        if to_create:
            self.edi_user_id._peppol_create_services(to_create)
        if to_update:
            self.edi_user_id._peppol_update_services(to_update)

        return res

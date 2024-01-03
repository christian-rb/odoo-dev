# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class Users(models.Model):
    _inherit = 'res.users'

    l10n_ke_oscu_company_ids = fields.One2many('res.company', compute='_compute_l10n_ke_oscu_company_ids')

    @api.depends('company_ids')
    def _compute_l10n_ke_oscu_company_ids(self):
        for user in self:
            user.l10n_ke_oscu_company_ids = user.company_ids.filtered(
                lambda company: all((
                    company.country_code == 'KE',
                    company.l10n_ke_oscu_is_active,
                    company.vat,
                ))
            )

    def action_l10n_ke_create_branch_user(self): # TODO - this is (again) just called with a button.. maybe it's better to do this automatically in the background
        for user in self:
            for company in user.l10n_ke_oscu_company_ids:
                error, data, dummy = company._l10n_ke_call_etims('saveBhfUser', {
                    'userId': user.id,
                    'userNm': user.login,
                    'pwd':    'test',
                    'useYn':  'Y',
                    'regrId': self.env.user.id,
                    'regrNm': self.env.user.name,
                    'modrId': self.env.user.id,
                    'modrNm': self.env.user.name,
                })
        if error:
            raise UserError(error)

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_ke_oscu_last_fetch_customs_import_date = fields.Char(default='20180101000000')

    def _l10n_ke_get_sar_sequence(self):
        """Returns the 'stored and released' sequence of a given company, and creates it if one is not yet defined."""
        self.ensure_one()
        if not (sequence := self.env['ir.sequence'].search([
            ('code', '=', 'l10n.ke.oscu.stock.sequence'),
            ('company_id', '=', self.id),
        ])):
            return self.env['ir.sequence'].create({
                'name': 'eTIMS Store and Release Number',
                'implementation': 'no_gap',
                'company_id': self.id,
                'code':  'l10n.ke.oscu.stock.sequence',
            })
        return sequence

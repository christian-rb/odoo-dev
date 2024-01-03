# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    l10n_ke_oscu_branch_code = fields.Char('Branch Code', default='00')

    def _l10n_ke_oscu_partner_content(self):
        """Returns a dict with the commonly required fields on partner for requests to the OSCU """
        self.ensure_one()
        return {
            'custNo':  self.id,                              # Customer Number
            'custTin': self.vat,                             # Customer PIN
            'custNm':  self.name,                            # Customer Name
            'adrs':    self.contact_address_inline or None,  # Address
            'email':   self.email or None,                   # Email
            'useYn':   'Y' if self.active else 'N',          # Used (Y/N)
        }

    def action_l10n_ke_oscu_register_bhf_customer(self):
        """Save the partner information on the OSCU."""
        for partner in self:
            content = {
                **self.env.company._l10n_ke_get_user_dict(partner.create_uid, partner.write_uid),
                **partner._l10n_ke_oscu_partner_content()    # Partner details
            }
            company = partner.company_id or self.env.company
            error, data, dummy = company._l10n_ke_call_etims('saveBhfCustomer', content)
            if error:
                raise UserError(f"[{error['code']}] {error['message']}")

    def action_l10n_ke_oscu_fetch_bhf_customer(self): # TODO - Inspect this endpoint. Determine whether we can make use of it. If not, remove this.
        company = self.company_id or self.env.company
        error, data, dummy = company._l10n_ke_call_etims('selectCustomer', {'custmTin': self.vat})
        raise UserError(data or error) # TODO: update fields on partner

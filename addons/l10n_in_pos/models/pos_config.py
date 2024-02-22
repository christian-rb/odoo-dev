# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, models
from odoo.exceptions import RedirectWarning, UserError
from odoo.tools.translate import _


class PosConfig(models.Model):
    _inherit = 'pos.config'

    def open_ui(self):
        for config in self:
            if config.company_id.country_id.code == 'IN' and not config.company_id.state_id:
                msg = _("Your company %s needs to have a correct address in order to open the session.\n"
                "Set the address of your company (Don't forget the State field)") % (config.company_id.name)
                action = {
                    "view_mode": "form",
                    "res_model": "res.company",
                    "type": "ir.actions.act_window",
                    "res_id" : config.company_id.id,
                    "views": [[self.env.ref("base.view_company_form").id, "form"]],
                }
                raise RedirectWarning(msg, action, _('Go to Company configuration'))
        return super(PosConfig, self).open_ui()

    @api.constrains('is_closing_entry_by_product')
    def _check_journal_entry_with_product_line(self):
        for config in self:
            if config.company_id.country_code == 'IN' and not config.is_closing_entry_by_product:
                raise UserError("You can't deactivate the 'Closing Entry by product' option for Indian Companies.")


    @api.model_create_multi
    def create(self, vals_list):
        for vals in list(vals_list):
            if self.env.company.country_code == 'IN':
                vals.update({
                    'is_closing_entry_by_product': True
                })
        pos_configs = super().create(vals_list)
        return pos_configs

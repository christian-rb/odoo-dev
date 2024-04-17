# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_default_xyz_partner(self, xyz):
        partner = self.partner_id
        if not partner:
            return False

        return self.env['res.partner'].browse(partner.address_get([xyz])[xyz])

    @api.model
    def _get_default_invoice_partner(self):
        return self._get_default_xyz_partner('invoice')

    @api.model
    def _get_default_delivery_partner(self):
        return self._get_default_xyz_partner('delivery')

    invoice_partner_id = fields.Many2one('res.partner', readonly=True, tracking=True,
        states={'draft': [('readonly', False)]},
        check_company=True, default=_get_default_invoice_partner,
        string='Invoice Address', index=True, change_default=True, ondelete='restrict')
    delivery_partner_id = fields.Many2one('res.partner', readonly=True, tracking=True,
        states={'draft': [('readonly', False)]},
        check_company=True, default=_get_default_delivery_partner,
        string='Delivery Address', index=True, change_default=True, ondelete='restrict')

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for record in self:
            if not record.delivery_partner_id:
                record.write({'delivery_partner_id': record._get_default_xyz_partner('delivery')})

            if not record.invoice_partner_id:
                record.write({'invoice_partner_id': record._get_default_xyz_partner('invoice')})

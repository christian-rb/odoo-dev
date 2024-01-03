# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, _


class Uom(models.Model):
    _inherit = 'uom.uom'


    l10n_ke_quantity_unit_id = fields.Many2one(
        'l10n_ke_edi_oscu.code',
        readonly=False,
        string='Quantity Unit',
        domain=[('code_type', '=', '10')],
        help='KRA code that describes the type of unit used.',
    )

    def _l10n_ke_get_validation_messages(self):# TODO - docstring
        misconfigured_uoms = self.filtered(lambda u: not u.l10n_ke_quantity_unit_id)
        return {
            'message': _('Some units of measure are missing a corresponding KRA code where one must be configured. '),
            'action_text': _("View UoM(s)"),
            'action': self._l10n_ke_action_open_uoms(misconfigured_uoms.ids),
            'blocking': True,
        } if misconfigured_uoms else {}

    def _l10n_ke_action_open_uoms(self, res_ids, title=None): # TODO - docstring
        if not isinstance(res_ids, tuple | list):
            res_ids = [res_ids]
        res = {
            'name': title or _("UoM(s)"),
            'type': 'ir.actions.act_window',
            'res_model': 'uom.uom',
            'domain': [('id', 'in', res_ids)],
            'view_mode': 'tree',
            'views': [(self.env.ref('l10n_ke_edi_oscu.product_uom_l10n_ke_tree').id, 'tree'), (False, 'form')],
            'context': {'create': False, 'delete': False},
        }
        return res

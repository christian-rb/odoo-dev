# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class BaseDocumentLayout(models.TransientModel):
    _inherit = 'base.document.layout'

    def _compute_preview(self):
        """ This override is needed to add the current document data to generate the preview """

        if self.env.context.get('active_model') != 'sale.order':
            return super()._compute_preview()
        order = self.env['sale.order'].browse(self.env.context.get('active_id'))
        if not order.exists():
            return super()._compute_preview()

        styles = self._get_asset_style()
        for wizard in self:
            if wizard.report_layout_id:
                wizard.preview = wizard.env['ir.ui.view']._render_template(
                    'sale.report_sale_order_wizard_iframe',
                    {
                        **wizard._get_render_information(styles),
                        'doc': order,
                    },
                )

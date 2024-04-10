# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    opportunity_id = fields.Many2one(
        'crm.lead', string='Opportunity', check_company=True,
        domain="[('type', '=', 'opportunity'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    def action_confirm(self):
        return super(SaleOrder, self.with_context({k:v for k,v in self._context.items() if k != 'default_tag_ids'})).action_confirm()

    def message_post(self, **kwargs):
        if not hasattr(self, 'recurring_total'):
            for record in self.opportunity_id:
                record.expected_revenue = record.expected_revenue or 0
                uncomfirmed_order_ids = record.order_ids.filtered(lambda x: x.state == "sent")
                if self.state == 'draft':
                    uncomfirmed_order_ids += self
                if uncomfirmed_order_ids:
                    new_expected_revenue = min(uncomfirmed_order_ids.mapped(lambda x: x.tax_totals['amount_untaxed']))
                if record.expected_revenue < new_expected_revenue:
                    record.expected_revenue = new_expected_revenue
        return super().message_post(**kwargs)

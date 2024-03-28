# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import itertools
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_is_zero
from odoo.tools.misc import groupby


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    value = fields.Monetary('Value', compute='_compute_value', groups='stock.group_stock_manager')
    currency_id = fields.Many2one('res.currency', compute='_compute_value', groups='stock.group_stock_manager')
    accounting_date = fields.Date(
        'Accounting Date',
        help="Date at which the accounting entries will be created"
             " in case of automated inventory valuation."
             " If empty, the inventory date will be used.")
    cost_method = fields.Selection(related="product_categ_id.property_cost_method")

    @api.model_create_multi
    def create(self, vals_list):
        valid_vals = [vals for vals in vals_list if 'lot_id' in vals]
        all_product_ids = [vals['product_id'] for vals in valid_vals]
        all_location_ids = [vals['location_id'] for vals in valid_vals]
        all_lot_ids = [vals['lot_id'] for vals in valid_vals]
        # get all the duplicate quants which will not create new quant rather will update existing one
        duplicate_quants = []
        if len(all_product_ids) > 0:
            duplicate_quants = self.search([
                ('product_id', 'in', all_product_ids),
                ('location_id', 'in', all_location_ids),
                ('lot_id', 'in', all_lot_ids)])
        quants = super().create(vals_list)

        duplicate_quants_ids = [q.id for q in duplicate_quants]
        # filter out all duplicates since these will not create new quants, update existing one
        quants_of_tracked_product = quants.filtered(lambda q: q.tracking in ['lot', 'serial'] and q.id not in duplicate_quants_ids)
        product_ids = [q.product_id.id for q in quants_of_tracked_product]
        location_ids = [q.location_id.id for q in quants_of_tracked_product]

        nearest_date_quants = self.search([
            ('product_id', 'in', product_ids),
            ('location_id', 'in', location_ids),
            ('accounting_date', '<', fields.Date().today())], order='accounting_date desc')
        quant_groups = {}
        for quant in nearest_date_quants:
            key = (quant.product_id.id, quant.location_id.id)
            if key not in quant_groups or quant.accounting_date > quant_groups[key].accounting_date:
                quant_groups[key] = quant

        for quant in quants_of_tracked_product:
            # nearest_date == date which is closest from today in past
            key = (quant.product_id.id, quant.location_id.id)
            if key in quant_groups:
                quant.accounting_date = quant_groups[key].accounting_date
        return quants

    def action_apply_inventory(self):
        # set the accounting date for quants if all quants have same product and location and quant have tracking product
        # first check all quants are similar(same product and location) and tracked
        product_id = list({quant.product_id for quant in self})
        location_id = list({quant.location_id for quant in self})
        if len(product_id) == 1 and len(location_id) == 1 and product_id[0].tracking in ['lot', 'serial']:
            nearest_date = self.search([
                ('product_id', '=', product_id[0].id),
                ('location_id', '=', location_id[0].id),
                ('accounting_date', '<', fields.Date().today())], order='accounting_date desc', limit=1).accounting_date
            if nearest_date:
                self.write({"accounting_date": nearest_date})
        return super().action_apply_inventory()

    @api.model
    def _should_exclude_for_valuation(self):
        """
        Determines if a quant should be excluded from valuation based on its ownership.
        :return: True if the quant should be excluded from valuation, False otherwise.
        """
        self.ensure_one()
        return self.owner_id and self.owner_id != self.company_id.partner_id

    @api.depends('company_id', 'location_id', 'owner_id', 'product_id', 'quantity')
    def _compute_value(self):
        """ (Product.value_svl / Product.quantity_svl) * quant.quantity, i.e. average unit cost * on hand qty
        """
        for quant in self:
            quant.currency_id = quant.company_id.currency_id
            if not quant.location_id or not quant.product_id or\
                    not quant.location_id._should_be_valued() or\
                    quant._should_exclude_for_valuation() or\
                    float_is_zero(quant.quantity, precision_rounding=quant.product_id.uom_id.rounding):
                quant.value = 0
                continue
            quantity = quant.product_id.with_company(quant.company_id).quantity_svl
            if float_is_zero(quantity, precision_rounding=quant.product_id.uom_id.rounding):
                quant.value = 0.0
                continue
            quant.value = quant.quantity * quant.product_id.with_company(quant.company_id).value_svl / quantity

    def _read_group_select(self, aggregate_spec, query):
        # flag value as aggregatable, and manually sum the values from the
        # records in the group
        if aggregate_spec == 'value:sum':
            return super()._read_group_select('id:recordset', query)
        return super()._read_group_select(aggregate_spec, query)

    def _read_group_postprocess_aggregate(self, aggregate_spec, raw_values):
        if aggregate_spec == 'value:sum':
            column = super()._read_group_postprocess_aggregate('id:recordset', raw_values)
            return (sum(records.mapped('value')) for records in column)
        return super()._read_group_postprocess_aggregate(aggregate_spec, raw_values)

    def _apply_inventory(self):
        for accounting_date, inventory_ids in groupby(self, key=lambda q: q.accounting_date):
            inventories = self.env['stock.quant'].concat(*inventory_ids)
            if accounting_date:
                super(StockQuant, inventories.with_context(force_period_date=accounting_date))._apply_inventory()
                inventories.accounting_date = False
            else:
                super(StockQuant, inventories)._apply_inventory()

    def _get_inventory_move_values(self, qty, location_id, location_dest_id, package_id=False, package_dest_id=False):
        res_move = super()._get_inventory_move_values(qty, location_id, location_dest_id, package_id, package_dest_id)
        if not self.env.context.get('inventory_name'):
            force_period_date = self.env.context.get('force_period_date', False)
            if force_period_date:
                res_move['name'] += _(' [Accounted on %s]', force_period_date)
        return res_move

    @api.model
    def _get_inventory_fields_write(self):
        """ Returns a list of fields user can edit when editing a quant in `inventory_mode`."""
        res = super()._get_inventory_fields_write()
        res += ['accounting_date']
        return res

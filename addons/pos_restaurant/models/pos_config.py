# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import json
from collections import defaultdict
from odoo.tools import convert


class PosConfig(models.Model):
    _inherit = 'pos.config'

    iface_splitbill = fields.Boolean(string='Bill Splitting', help='Enables Bill Splitting in the Point of Sale.')
    iface_printbill = fields.Boolean(string='Bill Printing', help='Allows to print the Bill before payment.')
    floor_ids = fields.Many2many('restaurant.floor', string='Restaurant Floors', help='The restaurant floors served by this point of sale.')
    set_tip_after_payment = fields.Boolean('Set Tip After Payment', help="Adjust the amount authorized by payment terminals to add a tip after the customers left or at the end of the day.")
    module_pos_restaurant_appointment = fields.Boolean("Table Booking")
    takeaway = fields.Boolean("Takeaway", help="Allow to create orders for takeaway customers.")
    takeaway_fp_id = fields.Many2one(
        'account.fiscal.position',
        string='Alternative Fiscal Position',
        help='This is useful for restaurants with onsite and take-away services that imply specific tax rates.',
    )

    def get_tables_order_count_and_printing_changes(self):
        self.ensure_one()
        floors = self.env['restaurant.floor'].search([('pos_config_ids', '=', self.id)])
        tables = self.env['restaurant.table'].search([('floor_id', 'in', floors.ids)])
        domain = [('state', '=', 'draft'), ('table_id', 'in', tables.ids)]

        order_stats = self.env['pos.order']._read_group(domain, ['table_id'], ['__count'])
        linked_orderlines = self.env['pos.order.line'].search([('order_id.state', '=', 'draft'), ('order_id.table_id', 'in', tables.ids)])
        orders_map = {table.id: count for table, count in order_stats}
        changes_map = defaultdict(lambda: 0)
        skip_changes_map = defaultdict(lambda: 0)

        for line in linked_orderlines:
            # For the moment, as this feature is not compatible with pos_self_order,
            # we ignore last_order_preparation_change when it is set to false.
            # In future, pos_self_order will send the various changes to the order.
            if not line.order_id.last_order_preparation_change:
                line.order_id.last_order_preparation_change = '{}'

            last_order_preparation_change = json.loads(line.order_id.last_order_preparation_change)
            prep_change = {}
            for line_uuid in last_order_preparation_change:
                prep_change[last_order_preparation_change[line_uuid]['line_uuid']] = last_order_preparation_change[line_uuid]
            quantity_changed = 0
            if line.uuid in prep_change:
                quantity_changed = line.qty - prep_change[line.uuid]['quantity']
            else:
                quantity_changed = line.qty

            if line.skip_change:
                skip_changes_map[line.order_id.table_id.id] += quantity_changed
            else:
                changes_map[line.order_id.table_id.id] += quantity_changed

        result = []
        for table in tables:
            result.append({'id': table.id, 'orders': orders_map.get(table.id, 0), 'changes': changes_map.get(table.id, 0), 'skip_changes': skip_changes_map.get(table.id, 0)})
        return result

    def _get_forbidden_change_fields(self):
        forbidden_keys = super(PosConfig, self)._get_forbidden_change_fields()
        forbidden_keys.append('floor_ids')
        return forbidden_keys

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            is_restaurant = 'module_pos_restaurant' in vals and vals['module_pos_restaurant']
            if is_restaurant and 'iface_splitbill' not in vals:
                vals['iface_splitbill'] = True
            if not is_restaurant or not vals.get('iface_tipproduct', False):
                vals['set_tip_after_payment'] = False
        pos_configs = super().create(vals_list)
        for config in pos_configs:
            if config.module_pos_restaurant:
                self._setup_default_floor(config)
        return pos_configs

    def write(self, vals):
        if ('module_pos_restaurant' in vals and vals['module_pos_restaurant'] is False):
            vals['floor_ids'] = [(5, 0, 0)]

        if ('module_pos_restaurant' in vals and not vals['module_pos_restaurant']) or ('iface_tipproduct' in vals and not vals['iface_tipproduct']):
            vals['set_tip_after_payment'] = False

        if ('module_pos_restaurant' in vals and vals['module_pos_restaurant']):
            self._setup_default_floor(self)

        return super().write(vals)

    def _setup_default_floor(self, pos_config):
        if not pos_config.floor_ids:
            main_floor = self.env['restaurant.floor'].create({
                'name': pos_config.company_id.name,
                'pos_config_ids': [(4, pos_config.id)],
            })
            self.env['restaurant.table'].create({
                'name': '1',
                'floor_id': main_floor.id,
                'seats': 1,
                'position_h': 100,
                'position_v': 100,
                'width': 100,
                'height': 100,
            })

    @api.model
    def load_onboarding_bar_scenario(self):
        convert.convert_file(self.env, 'pos_restaurant', 'data/scenarios/bar_data.xml', None, noupdate=True, mode='init', kind='data')
        journal, payment_methods_ids = self._create_journal_and_payment_methods()
        payment_methods_ids += self.env['pos.payment.method']._ensure_payment_methods([
            {'name': 'Cash bar', 'type': 'cash', 'ref': 'pos_restaurant.cash_payment_method_bar'}
        ])
        bar_categories = [
            self.env.ref('pos_restaurant.pos_category_cocktails').id,
            self.env.ref('pos_restaurant.pos_category_soft_drinks').id,
        ]
        config = self.env['pos.config'].create({
            'name': 'Bar',
            'company_id': self.env.company.id,
            'journal_id': journal.id,
            'payment_method_ids': payment_methods_ids,
            'limit_categories': True,
            'iface_available_categ_ids': bar_categories,
            'iface_splitbill': True,
            'module_pos_restaurant': True,
        })
        self.env['ir.model.data']._update_xmlids([{
            'xml_id': 'pos_restaurant.pos_config_main_bar',
            'record': config,
            'noupdate': True,
        }])

    @api.model
    def load_onboarding_restaurant_scenario(self):
        convert.convert_file(self.env, 'pos_restaurant', 'data/scenarios/restaurant_data.xml', None, noupdate=True, mode='init', kind='data')
        journal, payment_methods_ids = self._create_journal_and_payment_methods()
        payment_methods_ids += self.env['pos.payment.method']._ensure_payment_methods([
            {'name': 'Cash restaurant', 'type': 'cash', 'ref': 'pos_restaurant.cash_payment_method_restaurant'}
        ])
        restaurant_categories = [
            self.env.ref('pos_restaurant.food').id,
            self.env.ref('pos_restaurant.drinks').id,
        ]
        config = self.env['pos.config'].create({
            'name': 'Restaurant',
            'company_id': self.env.company.id,
            'journal_id': journal.id,
            'payment_method_ids': payment_methods_ids,
            'limit_categories': True,
            'iface_available_categ_ids': restaurant_categories,
            'iface_splitbill': True,
            'module_pos_restaurant': True,
        })
        self.env['ir.model.data']._update_xmlids([{
            'xml_id': 'pos_restaurant.pos_config_main_restaurant',
            'record': config,
            'noupdate': True,
        }])
        if self.env.company.id == self.env.ref('base.main_company').id:
            self._load_demo_orders()

    @api.model
    def _load_demo_orders(self):
        existing_session = self.env.ref('pos_restaurant.pos_closed_session_3', raise_if_not_found=False)
        if existing_session:
            return
        convert.convert_file(self.env, 'pos_restaurant', 'data/restaurant_session_floor.xml', None, noupdate=True, mode='init', kind='data')

    def _create_journal_and_payment_methods(self):
        journal = self.env['account.journal']._ensure_company_account_journal()
        payment_methods_ids = self.env['pos.payment.method']._ensure_payment_methods([
            {'name': 'Bank', 'type': 'bank', 'ref': 'pos_restaurant.bank_payment_method'},
            {'name': 'Customer Account', 'type': 'pay_later', 'ref': 'pos_restaurant.customer_payment_method'},
        ])
        return journal, payment_methods_ids

    @api.model
    def load_onboarding_pos_config_restaurant(self):
        journal, payment_methods_ids = self._create_journal_and_payment_methods()
        payment_methods_ids += self.env['pos.payment.method']._ensure_payment_methods([
            {'name': 'Cash restaurant', 'type': 'cash', 'ref': 'point_of_sale.cash_payment_method_restaurant'}
        ])
        self.env['pos.config'].create({
            'name': 'Restaurant',
            'company_id': self.env.company.id,
            'journal_id': journal.id,
            'payment_method_ids': payment_methods_ids,
            'module_pos_restaurant': True,
        })

    @api.model
    def load_onboarding_pos_config_kiosk(self):
        journal, payment_methods_ids = self._create_journal_and_payment_methods()
        payment_methods_ids += self.env['pos.payment.method']._ensure_payment_methods([
            {'name': 'Cash kiosk', 'type': 'cash', 'ref': 'point_of_sale.cash_payment_method_kiosk'}
        ])
        # TODO-manv: ask moda on how to config kiosk
        self.env['pos.config'].create({
            'name': 'Kiosk: self-order',
            'company_id': self.env.company.id,
            'journal_id': journal.id,
            'payment_method_ids': payment_methods_ids,
            'module_pos_restaurant': True,
        })

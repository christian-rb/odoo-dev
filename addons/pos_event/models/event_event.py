from odoo import api, fields, models
from itertools import groupby
from operator import itemgetter
from functools import reduce
from collections import defaultdict


class Event(models.Model):
    _name = 'event.event'
    _inherit = ['event.event', 'pos.load.mixin']

    pos_order_lines_ids = fields.One2many('pos.order.line', 'event_id', string="All pos order lines pointing to this event")
    pos_price_subtotal = fields.Monetary("PoS sales (Tax Excluded)", compute='_compute_pos_price_subtotal')
    image = fields.Image("Image", max_width=1024, max_height=1024)

    @api.model
    def _load_pos_data_domain(self, data):
        return [('is_finished', '=', False), ('is_ongoing', '=', False), ('event_ticket_ids', '!=', False)]

    @api.model
    def _load_pos_data_fields(self, config_id):
        return ['id', 'name', 'seats_available', 'event_ticket_ids', 'registration_ids', 'seats_limited']

    def _load_pos_data(self, data):
        domain = self._load_pos_data_domain(data)
        fields = self._load_pos_data_fields(data['pos.config']['data'][0]['id'])
        return {
            'data': self.sudo().search_read(domain, fields, load=False),
            'fields': fields,
        }

    @api.depends('company_id.currency_id', 'pos_order_lines_ids', 'pos_order_lines_ids.currency_id')
    def _compute_pos_price_subtotal(self):
        """ Takes all the pos.order.lines related to this event and converts amounts
        from the currency of the pos orders to the currency of the event company.
        To avoid extra overhead, we use conversion rates as of 'today'.
        Meaning we have a number that can change over time, but using the conversion rates
        at the time of the related pos.order would mean thousands of extra requests as we would
        have to do one conversion per pos.order"""
        date_now = fields.Datetime.now()
        subtotal_by_event = defaultdict(lambda: 0)
        if self.ids:
            keys = itemgetter('event_id', 'currency_id')
            order_lines = self.env['pos.order.line'].search_read(
                [('event_id', 'in', self.ids), ('price_subtotal', '!=', 0)],
                ['event_id', 'currency_id', 'price_subtotal'],
                load=False)

            event_subtotals = []
            currency_id_set = set()
            for k, g in groupby(sorted(order_lines, key=keys), key=keys):
                lines = list(g)
                event_id, currency_id = k
                event_subtotals.append({
                    'event_id': event_id,
                    'currency_id': currency_id,
                    'subtotal': reduce(lambda accumulator, line: accumulator + line['price_subtotal'], lines, 0)
                })
                currency_id_set.add(currency_id)

            event_data = {}
            for event in self:
                event_data[event.id] = {
                    'company_id': event.company_id,
                    'currency_id': event.currency_id,
                }

            currency_by_id = {currency.id: currency for currency in self.env['res.currency'].browse(currency_id_set)}

            for event_subtotal in event_subtotals:
                event_id = event_subtotal['event_id']
                currency_id = event_subtotal['currency_id']
                price = event_data[event_id]['currency_id']._convert(
                    event_subtotal['subtotal'],
                    currency_by_id[currency_id],
                    event_data[event_id]['company_id'],
                    date_now)

                subtotal_by_event[event_id] += price

        for event in self:
            event.pos_price_subtotal = subtotal_by_event[event.id]

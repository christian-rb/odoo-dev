from odoo import fields, models, api


class EventRegistration(models.Model):
    _name = 'event.registration'
    _inherit = ['event.registration', 'pos.load.mixin']

    pos_order_id = fields.Many2one(related='pos_order_line_id.order_id', string='PoS Order')
    pos_order_line_id = fields.Many2one('pos.order.line', string='PoS Order Line', ondelete='cascade', copy=False)

    def _load_pos_data(self, data):
        domain = self._load_pos_data_domain(data)
        fields = self._load_pos_data_fields(data['pos.config']['data'][0]['id'])
        return {
            'data': self.sudo().search_read(domain, fields, load=False),
            'fields': fields,
        }

    @api.model
    def _load_pos_data_domain(self, data):
        return [('event_ticket_id', 'in', [ticket['id'] for ticket in data['event.event.ticket']['data']])]

    @api.model
    def _load_pos_data_fields(self, config_id):
        return ['id', 'event_id', 'event_ticket_id', 'pos_order_line_id', 'pos_order_id']

    @api.depends('pos_order_id.state', 'pos_order_line_id.currency_id', 'pos_order_line_id.price_subtotal_incl')
    def _compute_registration_status(self):
        super()._compute_registration_status()

    def _get_order(self):
        if self.pos_order_line_id:
            return self.pos_order_line_id
        return super()._get_order()

    def _is_cancel(self):
        return self.pos_order_id.state == 'cancel'

    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)
        result._update_available_seat()
        return result

    def write(self, vals):
        result = super().write(vals)
        self._update_available_seat()
        return result

    def _update_available_seat(self):
        # Here sudo is used in order for pos_event to update the available seats to all open pos session when a ticket is sold in website for example
        session_ids = self.env['pos.session'].sudo().search([("state", "!=", "closed")])
        session_ids.config_id._update_events_seats([self.event_id])

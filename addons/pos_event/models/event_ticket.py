from odoo import models, api


class EventTicket(models.Model):
    _name = 'event.event.ticket'
    _inherit = ['event.event.ticket', 'pos.load.mixin']

    @api.model
    def _load_pos_data_domain(self, data):
        return [('event_id', 'in', [event['id'] for event in data['event.event']['data']])]

    def _load_pos_data(self, data):
        domain = self._load_pos_data_domain(data)
        fields = self._load_pos_data_fields(data['pos.config']['data'][0]['id'])
        return {
            'data': self.sudo().search_read(domain, fields, load=False),
            'fields': fields,
        }

    @api.model
    def _load_pos_data_fields(self, config_id):
        return ['id', 'name', 'event_id', 'seats_used', 'seats_available', 'product_id']

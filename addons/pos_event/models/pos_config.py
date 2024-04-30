from odoo import models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    def _update_events_seats(self, events):
        for record in self:
            record._notify('UPDATE_AVAILABLE_SEATS', [{
                'event_id': event.id,
                'seats_available': event.seats_available,
                'event_ticket_ids': [{
                    'ticket_id': ticket.id,
                    'seats_available': ticket.seats_available
                } for ticket in event.event_ticket_ids]
            } for event in events])

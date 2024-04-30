from odoo import models, fields, api


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    event_id = fields.Many2one('event.event', string='Event', compute="_compute_event_id", store=True, precompute=True)
    event_ticket_id = fields.Many2one('event.event.ticket', string='Event Ticket')
    event_registration_ids = fields.One2many('event.registration', 'pos_order_line_id', string='Event Registrations')

    @api.depends('event_registration_ids')
    def _compute_event_id(self):
        for line in self:
            line.event_id = line.event_registration_ids.event_id

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields = super()._load_pos_data_fields(config_id)
        fields += ['event_id', 'event_ticket_id', 'event_registration_ids']
        return fields

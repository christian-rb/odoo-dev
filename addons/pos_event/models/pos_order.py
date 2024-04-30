from odoo import models, fields, api


class PosOrder(models.Model):
    _inherit = 'pos.order'

    attendee_count = fields.Integer('Attendee Count', compute='_compute_attendee_count')

    @api.depends('lines.event_registration_ids')
    def _compute_attendee_count(self):
        for order in self:
            order.attendee_count = len(order.lines.mapped('event_registration_ids'))

    def action_view_attendee_list(self):
        action = self.env["ir.actions.actions"]._for_xml_id("event.event_registration_action_tree")
        action['domain'] = [('pos_order_id', 'in', self.ids)]
        return action

    @api.model
    def sync_from_ui(self, orders):
        results = super().sync_from_ui(orders)
        paid_orders = self.browse([order['id'] for order in results['pos.order'] if order['state'] in ['paid', 'done', 'invoiced']])

        if not paid_orders:
            return results

        line_with_event = paid_orders.mapped('lines').filtered(lambda line: line.event_ticket_id)
        for line in line_with_event:
            for _count in range(int(line.qty)):
                line.event_registration_ids.create({
                    'pos_order_line_id': line.id,
                    'pos_order_id': line.order_id.id,
                    'event_id': line.event_ticket_id.event_id.id,
                    'event_ticket_id': line.event_ticket_id.id,
                    'partner_id': line.order_id.partner_id.id or False,
                })

        event_registrations = line_with_event.mapped('event_registration_ids')
        event_registrations_dict = event_registrations.read(self.env['event.registration']._load_pos_data_fields(paid_orders[0].config_id.id), load=False)
        results['event.registration'] = event_registrations_dict
        return results

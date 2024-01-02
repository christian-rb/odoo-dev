from odoo import models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def action_sent_message_on_sms(self, phoneNumber):
        """ Send message on sms if sms is enabled and partner has mobile number or number is provided."""
        if not (self and self.config_id.module_pos_sms and self.config_id.sms_receipt_template_id and phoneNumber):
            return
        self.ensure_one()
        sms_composer = self.env['sms.composer'].with_context(active_id=self.id).create(
            {
                'composition_mode': 'numbers',
                'numbers': phoneNumber,
                'template_id': self.config_id.sms_receipt_template_id.id,
                'res_model': 'pos.order'
            }
        )
        sms_composer.action_send_sms()

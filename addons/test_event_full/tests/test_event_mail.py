# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from freezegun import freeze_time

from odoo.addons.mail.tests.common import MockEmail
from odoo.addons.sms.tests.common import MockSMS
from odoo.addons.test_event_full.tests.common import TestWEventCommon

class TestEventSmsMailSchedule(TestWEventCommon, MockEmail, MockSMS):

    @freeze_time('2020-07-06 12:00:00')
    def test_event_mail_before_trigger_sent_count(self):
        """ Emails are sent to both confirmed and unconfirmed attendees.
        This test checks that the count of sent emails includes the emails sent to unconfirmed ones

        Time in the test is frozen to simulate the following state:

                   NOW     Event Start    Event End
                  12:00       13:00        14:00
                    |           |            |
            ──────────────────────────────────────►
            |                   |                time
            ◄─────────────────►
                  3 hours
              Trigger before event
        """
        self.sms_template_rem = self.env['sms.template'].create({
            'name': 'Test reminder',
            'model_id': self.env.ref('event.model_event_registration').id,
            'body': '{{ object.event_id.organizer_id.name }} reminder',
            'lang': '{{ object.partner_id.lang }}'
        })
        test_event = self.env['event.event'].create({
            'name': 'TestEventMail',
            # 'user_id': self.env.ref('base.user_admin').id,
            'date_begin': datetime.now() + timedelta(hours=1),
            'date_end': datetime.now() + timedelta(hours=2),
            'event_mail_ids': [
                (0, 0, {  # email 3 hours before event
                    'interval_nbr': 3,
                    'interval_unit': 'hours',
                    'interval_type': 'before_event',
                    'template_ref': 'mail.template,%i' % self.env['ir.model.data']._xmlid_to_res_id('event.event_reminder')}),
                (0, 0, {  # sms 3 hours before event
                    'interval_nbr': 3,
                    'interval_unit': 'hours',
                    'interval_type': 'before_event',
                    'notification_type': 'sms',
                    'template_ref': 'sms.template,%i' % self.sms_template_rem.id}),
            ]
        })
        mail_scheduler = test_event.event_mail_ids
        self.assertEqual(len(mail_scheduler), 2, 'There should be two mail schedulers. One for mail one for sms. Cannot perform test')

        # Add registrations
        self.env['event.registration'].create([{
            'event_id': test_event.id,
            'name': 'RegistrationUnconfirmed',
            'email': 'Registration@Unconfirmed.com',
            'state': 'draft',
        }, {
            'event_id': test_event.id,
            'name': 'RegistrationCanceled',
            'email': 'Registration@Canceled.com',
            'state': 'cancel',
        }, {
            'event_id': test_event.id,
            'name': 'RegistrationConfirmed',
            'email': 'Registration@Confirmed.com',
            'state': 'open',
        }])

        with self.mock_mail_gateway(), self.mockSMSGateway():
            mail_scheduler.execute()

        self.assertEqual(len(self._new_mails), 2, 'Mails were not created')
        self.assertEqual(len(self._new_sms), 2, 'SMS were not created')

        self.assertEqual(test_event.seats_taken, 1, 'Wrong number of seats_taken')

        self.assertEqual(mail_scheduler.filtered(lambda r: r.notification_type == 'mail').mail_count_done, 2,
            'Wrong Emails Sent Count! Probably emails sent to unconfirmed attendees were not included into the Sent Count')
        self.assertEqual(mail_scheduler.filtered(lambda r: r.notification_type == 'sms').mail_count_done, 2,
            'Wrong SMS Sent Count! Probably SMS sent to unconfirmed attendees were not included into the Sent Count')

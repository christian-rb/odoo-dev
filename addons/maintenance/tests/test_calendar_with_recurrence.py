from odoo.tests import HttpCase, tagged
from datetime import timedelta, date, datetime


@tagged('post_install', '-at_install')
class TestCalendarWithRecurrence(HttpCase):

    def test_edit_event_from_calendar(self):
        self.env['maintenance.team'].create({
            'name': 'the boys',
        })
        equipment = self.env['maintenance.equipment'].create({
            'name': 'bed'
        })
        self.env['maintenance.request'].create({
            'name': 'send the mails',
            'schedule_date': datetime.today() - timedelta(weeks=2),
        })
        request = self.env['maintenance.request'].create({
            'name': 'clean the room',
            'schedule_date': datetime.combine(date.today(), (datetime.min + timedelta(hours=10)).time()),  # today at 10.00 AM
            'equipment_id': equipment.id,  # necessary for the tour to work with mrp_maintenance installed
            'duration': 1,
        })
        self.env['maintenance.request'].create({
            'name': 'wash the car',
            'schedule_date': datetime.today() + timedelta(weeks=1),
        })

        action = self.env["ir.actions.actions"]._for_xml_id("maintenance.hr_equipment_request_action_cal")
        url = '/web?#action=%s' % (action['id'])
        self.start_tour(url, 'test_edit_event_from_calendar', login='admin')

        weekday = (date.today().weekday() + 1) % 7  # Sunday is the first day of the week in the calendar
        wednesday = 3 - weekday  # difference between Wednesday and today
        newHour = datetime.combine(
            date.today() + timedelta(days=wednesday),
            (datetime.min + timedelta(hours=13.25)).time()
        )  # this Wednesday at 1.15 PM
        self.assertEqual(request.name, 'make your bed')
        self.assertEqual(request.schedule_date, newHour)

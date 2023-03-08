# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged
from datetime import datetime
from odoo.addons.hr_calendar.tests.common import TestHrCalendarCommon


@tagged('work_hours')
class TestWorkingHours(TestHrCalendarCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_working_hours_2_emp_same_calendar(self):
        work_hours = self.env['hr.employee'].get_working_hours_for_all_attendees(
            [self.partnerA.id, self.partnerD.id],
            datetime(2023, 12, 25).isoformat(),
            datetime(2023, 12, 31).isoformat()
            )
        # Monday
        self.assertEqual(work_hours[0], {'daysOfWeek': [1], 'startTime': '08:00', 'endTime': '12:00'})
        self.assertEqual(work_hours[1], {'daysOfWeek': [1], 'startTime': '13:00', 'endTime': '16:00'})
        # Tuesday
        self.assertEqual(work_hours[2], {'daysOfWeek': [2], 'startTime': '08:00', 'endTime': '12:00'})
        self.assertEqual(work_hours[3], {'daysOfWeek': [2], 'startTime': '13:00', 'endTime': '16:00'})
        # Wednesday
        self.assertEqual(work_hours[4], {'daysOfWeek': [3], 'startTime': '08:00', 'endTime': '12:00'})
        self.assertEqual(work_hours[5], {'daysOfWeek': [3], 'startTime': '13:00', 'endTime': '16:00'})
        # Thursday
        self.assertEqual(work_hours[6], {'daysOfWeek': [4], 'startTime': '08:00', 'endTime': '12:00'})
        self.assertEqual(work_hours[7], {'daysOfWeek': [4], 'startTime': '13:00', 'endTime': '16:00'})
        # Friday
        self.assertEqual(work_hours[8], {'daysOfWeek': [5], 'startTime': '08:00', 'endTime': '12:00'})
        self.assertEqual(work_hours[9], {'daysOfWeek': [5], 'startTime': '13:00', 'endTime': '16:00'})

    def test_working_hours_2_emp_different_calendar(self):
        work_hours = self.env['hr.employee'].get_working_hours_for_all_attendees(
            [self.partnerA.id, self.partnerB.id],
            datetime(2023, 12, 25).isoformat(),
            datetime(2023, 12, 31).isoformat()
            )
        # Nothing on monday due to partnerB's calendar : calendar_28h

        # Tuesday
        self.assertEqual(work_hours[0], {'daysOfWeek': [2], 'startTime': '08:00', 'endTime': '12:00'})
        self.assertEqual(work_hours[1], {'daysOfWeek': [2], 'startTime': '13:00', 'endTime': '16:00'})
        # Wednesday
        self.assertEqual(work_hours[2], {'daysOfWeek': [3], 'startTime': '08:00', 'endTime': '12:00'})
        self.assertEqual(work_hours[3], {'daysOfWeek': [3], 'startTime': '13:00', 'endTime': '16:00'})
        # Thursday
        self.assertEqual(work_hours[4], {'daysOfWeek': [4], 'startTime': '08:00', 'endTime': '12:00'})
        self.assertEqual(work_hours[5], {'daysOfWeek': [4], 'startTime': '13:00', 'endTime': '16:00'})
        # Friday
        self.assertEqual(work_hours[6], {'daysOfWeek': [5], 'startTime': '08:00', 'endTime': '12:00'})
        self.assertEqual(work_hours[7], {'daysOfWeek': [5], 'startTime': '13:00', 'endTime': '16:00'})

    def test_working_hours_3_emp_different_calendar(self):
        work_hours = self.env['hr.employee'].get_working_hours_for_all_attendees(
            [self.partnerA.id, self.partnerB.id, self.partnerC.id],
            datetime(2023, 12, 25).isoformat(),
            datetime(2023, 12, 31).isoformat()
            )
        # Nothing on monday due to partnerB's calendar : calendar_28h
        # Nothing before 15:00 due to partnerC's calendar : calendar_28h_night

        # Tuesday
        self.assertEqual(work_hours[0], {'daysOfWeek': [2], 'startTime': '15:00', 'endTime': '16:00'})
        # Wednesday
        self.assertEqual(work_hours[1], {'daysOfWeek': [3], 'startTime': '15:00', 'endTime': '16:00'})
        # Thursday
        self.assertEqual(work_hours[2], {'daysOfWeek': [4], 'startTime': '15:00', 'endTime': '16:00'})
        # Friday
        self.assertEqual(work_hours[3], {'daysOfWeek': [5], 'startTime': '15:00', 'endTime': '16:00'})

    def test_working_hours_2_emp_same_calendar_hours_different_timezone(self):
        calendar_35h_london_tz = self.calendar_35h.copy()
        calendar_35h_london_tz.tz = 'Europe/London'
        self.employeeD.resource_calendar_id = calendar_35h_london_tz
        work_hours = self.env['hr.employee'].get_working_hours_for_all_attendees(
            [self.partnerA.id, self.partnerD.id],
            datetime(2023, 12, 25).isoformat(),
            datetime(2023, 12, 31).isoformat()
            )
        # calendar_35h_london_tz.tz = UTC, calendar_35h.tz = UTC +1

        # Monday
        self.assertEqual(work_hours[0], {'daysOfWeek': [1], 'startTime': '09:00', 'endTime': '12:00'})
        self.assertEqual(work_hours[1], {'daysOfWeek': [1], 'startTime': '14:00', 'endTime': '16:00'})
        # Tuesday
        self.assertEqual(work_hours[2], {'daysOfWeek': [2], 'startTime': '09:00', 'endTime': '12:00'})
        self.assertEqual(work_hours[3], {'daysOfWeek': [2], 'startTime': '14:00', 'endTime': '16:00'})
        # Wednesday
        self.assertEqual(work_hours[4], {'daysOfWeek': [3], 'startTime': '09:00', 'endTime': '12:00'})
        self.assertEqual(work_hours[5], {'daysOfWeek': [3], 'startTime': '14:00', 'endTime': '16:00'})
        # Thursday
        self.assertEqual(work_hours[6], {'daysOfWeek': [4], 'startTime': '09:00', 'endTime': '12:00'})
        self.assertEqual(work_hours[7], {'daysOfWeek': [4], 'startTime': '14:00', 'endTime': '16:00'})
        # Friday
        self.assertEqual(work_hours[8], {'daysOfWeek': [5], 'startTime': '09:00', 'endTime': '12:00'})
        self.assertEqual(work_hours[9], {'daysOfWeek': [5], 'startTime': '14:00', 'endTime': '16:00'})

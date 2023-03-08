# Part of Odoo. See LICENSE file for full copyright and licensing details.

from pytz import UTC, timezone
from datetime import datetime
from collections import defaultdict
from functools import reduce

from odoo import models

from odoo.addons.resource.models.utils import Intervals


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    def _get_calendar(self, start=None, stop=None):
        self.ensure_one()
        return self.resource_calendar_id or self.env.company.resource_calendar_id

    def _get_calendar_periods(self, start, stop):
        # This method can be overridden in other modules where it's possible
        # to have different resource calendars for an employee depending on the
        # date.
        self.ensure_one()
        return [(start, stop, self._get_calendar(start, stop))]

    def _get_employees_from_attendees(self, attendee_ids, everybody=False):
        if everybody:
            partners = self.env['res.partner'].browse([('employees_count', '>', 0)])
        else:
            partners = self.env['res.partner'].browse(attendee_ids)
        return partners.sudo().employee_ids.filtered(
            lambda employee: employee.company_id == self.env.company).sudo(False)

    def get_working_hours_for_all_attendees(self, attendee_ids, date_from, date_to, everybody=False):
        # This method implements the general case where employees might have
        # different resource calendars at different times, even though this is
        # not the case with only this module installed. This way it will work
        # with these other modules by just overriding `_get_calendar_periods`
        employees = self._get_employees_from_attendees(attendee_ids, everybody)
        if not employees:
            return []

        start_period = datetime.fromisoformat(date_from).replace(hour=0, minute=0, second=0, tzinfo=UTC)
        stop_period = datetime.fromisoformat(date_to).replace(hour=23, minute=59, second=59, tzinfo=UTC)

        interval_by_calendar = defaultdict()
        calendar_periods_by_employee = defaultdict(list)
        employees_by_calendar = defaultdict(list)
        for employee in employees:
            calendar_periods = employee._get_calendar_periods(start_period, stop_period)
            if not calendar_periods:
                return self._interval_to_business_hours([])

            for (start, stop, calendar) in calendar_periods:
                employees_by_calendar[calendar].append(employee)
            calendar_periods_by_employee[employee] = calendar_periods

        for calendar, employees in employees_by_calendar.items():
            work_intervals = calendar._work_intervals_batch(start_period, stop_period, resources=employees, tz=timezone(calendar.tz))
            del work_intervals[False]
            interval_by_calendar[calendar] = reduce(Intervals.__and__, work_intervals.values())

        schedules = []
        for employee, calendar_periods in calendar_periods_by_employee.items():
            employee_interval = Intervals([])
            for (start, stop, calendar) in calendar_periods:
                interval = Intervals([(start, stop, self.env['resource.calendar'])])
                employee_interval = employee_interval | (interval_by_calendar[calendar] & interval)
            schedules.append(employee_interval)

        return self._interval_to_business_hours(reduce(Intervals.__and__, schedules))

    def _interval_to_business_hours(self, working_intervals):
        # This is the format expected by the fullcalendar library to do the overlay
        return [{
            "daysOfWeek": [interval[0].weekday() + 1],
            "startTime":  interval[0].astimezone(timezone(self.env.user.tz)).strftime("%H:%M"),
            "endTime": interval[1].astimezone(timezone(self.env.user.tz)).strftime("%H:%M"),
            } for interval in working_intervals] if working_intervals else [{
                # 7 is used a dummy value to gray the full week
                # Returning an empty list would leave the week uncolored
                "daysOfWeek": [7],
                "startTime":  datetime.today().strftime("00:00"),
                "endTime": datetime.today().strftime("00:00"),
            }]

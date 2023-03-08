# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.resource.models.utils import Intervals, timezone_datetime, sum_intervals
from collections import defaultdict

from odoo import api, fields, models


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    unavailable_partner_ids = fields.Many2many('res.partner', compute='_compute_unavailable_partner_ids')

    def _get_event_interval(self):
        if self.allday:
            company_calendar = self.env.company.resource_calendar_id
            start = timezone_datetime(self.start.replace(hour=0, minute=0, second=0))
            stop = timezone_datetime(self.stop.replace(hour=23, minute=59, second=59))
            event_interval = company_calendar._work_intervals_batch(start, stop)[False]
        else:
            event_interval = Intervals([(
                    timezone_datetime(self.start),
                    timezone_datetime(self.stop),
                    self.env['resource.calendar']
                )])
        return event_interval

    @api.depends('partner_ids', 'start', 'stop', 'allday')
    def _compute_unavailable_partner_ids(self):
        for event in self:
            unavailable_employee_ids = []
            employees_by_calendar = defaultdict(list)

            event_interval = self._get_event_interval()
            start = event_interval._items[0][0]
            stop = event_interval._items[-1][1]

            employees = set(self.env['hr.employee']._get_employees_from_attendees(event.partner_ids.ids))

            for employee in employees:
                calendar = employee._get_calendar(start)
                if not calendar:
                    unavailable_employee_ids.append(employee.id)
                    continue
                employees_by_calendar[calendar].append(employee)

            for calendar, employees in employees_by_calendar.items():
                work_intervals = calendar._work_intervals_batch(start, stop, resources=employees)
                work_intervals.pop(False)
                for employee, intervals in work_intervals.items():
                    common_interval = intervals & event_interval
                    if sum_intervals(common_interval) != sum_intervals(event_interval):
                        unavailable_employee_ids.append(employee)

            event.unavailable_partner_ids = self.env['hr.employee'].browse(unavailable_employee_ids).work_contact_id

    @api.model
    def get_unusual_days(self, date_from, date_to=None):
        return self.env.user.employee_id._get_unusual_days(date_from, date_to)

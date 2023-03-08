# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import common


class TestHrCalendarCommon(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.tz = 'Europe/Brussels'

        cls.company = cls.env['res.company'].create({'name': 'Test company'})
        cls.env.user.company_id = cls.company

        cls.calendar_35h = cls.env['resource.calendar'].create({
            'company_id': cls.company.id,
            'tz': "Europe/Brussels",
            'name': '35h calendar',
            'hours_per_day': 7.0,
            'attendance_ids': [
                (0, 0, {'name': 'Monday Morning', 'dayofweek': '0', 'hour_from': 8, 'hour_to': 12, 'day_period': 'morning'}),
                (0, 0, {'name': 'Monday Lunch', 'dayofweek': '0', 'hour_from': 12, 'hour_to': 13, 'day_period': 'lunch'}),
                (0, 0, {'name': 'Monday Evening', 'dayofweek': '0', 'hour_from': 13, 'hour_to': 16, 'day_period': 'afternoon'}),
                (0, 0, {'name': 'Tuesday Morning', 'dayofweek': '1', 'hour_from': 8, 'hour_to': 12, 'day_period': 'morning'}),
                (0, 0, {'name': 'Tuesday Lunch', 'dayofweek': '1', 'hour_from': 12, 'hour_to': 13, 'day_period': 'lunch'}),
                (0, 0, {'name': 'Tuesday Evening', 'dayofweek': '1', 'hour_from': 13, 'hour_to': 16, 'day_period': 'afternoon'}),
                (0, 0, {'name': 'Wednesday Morning', 'dayofweek': '2', 'hour_from': 8, 'hour_to': 12, 'day_period': 'morning'}),
                (0, 0, {'name': 'Wednesday Lunch', 'dayofweek': '2', 'hour_from': 12, 'hour_to': 13, 'day_period': 'lunch'}),
                (0, 0, {'name': 'Wednesday Evening', 'dayofweek': '2', 'hour_from': 13, 'hour_to': 16, 'day_period': 'afternoon'}),
                (0, 0, {'name': 'Thursday Morning', 'dayofweek': '3', 'hour_from': 8, 'hour_to': 12, 'day_period': 'morning'}),
                (0, 0, {'name': 'Thursday Lunch', 'dayofweek': '3', 'hour_from': 12, 'hour_to': 13, 'day_period': 'lunch'}),
                (0, 0, {'name': 'Thursday Evening', 'dayofweek': '3', 'hour_from': 13, 'hour_to': 16, 'day_period': 'afternoon'}),
                (0, 0, {'name': 'Friday Morning', 'dayofweek': '4', 'hour_from': 8, 'hour_to': 12, 'day_period': 'morning'}),
                (0, 0, {'name': 'Friday Lunch', 'dayofweek': '4', 'hour_from': 12, 'hour_to': 13, 'day_period': 'lunch'}),
                (0, 0, {'name': 'Friday Evening', 'dayofweek': '4', 'hour_from': 13, 'hour_to': 16, 'day_period': 'afternoon'})
            ],
        })

        cls.calendar_28h = cls.env['resource.calendar'].create({
            'company_id': cls.company.id,
            'tz': "Europe/Brussels",
            'name': '28h calendar',
            'attendance_ids': [
                (0, 0, {'name': 'Tuesday Morning', 'dayofweek': '1', 'hour_from': 8, 'hour_to': 12, 'day_period': 'morning'}),
                (0, 0, {'name': 'Tuesday Lunch', 'dayofweek': '1', 'hour_from': 12, 'hour_to': 13, 'day_period': 'lunch'}),
                (0, 0, {'name': 'Tuesday Evening', 'dayofweek': '1', 'hour_from': 13, 'hour_to': 16, 'day_period': 'afternoon'}),
                (0, 0, {'name': 'Wednesday Morning', 'dayofweek': '2', 'hour_from': 8, 'hour_to': 12, 'day_period': 'morning'}),
                (0, 0, {'name': 'Wednesday Lunch', 'dayofweek': '2', 'hour_from': 12, 'hour_to': 13, 'day_period': 'lunch'}),
                (0, 0, {'name': 'Wednesday Evening', 'dayofweek': '2', 'hour_from': 13, 'hour_to': 16, 'day_period': 'afternoon'}),
                (0, 0, {'name': 'Thursday Morning', 'dayofweek': '3', 'hour_from': 8, 'hour_to': 12, 'day_period': 'morning'}),
                (0, 0, {'name': 'Thursday Lunch', 'dayofweek': '3', 'hour_from': 12, 'hour_to': 13, 'day_period': 'lunch'}),
                (0, 0, {'name': 'Thursday Evening', 'dayofweek': '3', 'hour_from': 13, 'hour_to': 16, 'day_period': 'afternoon'}),
                (0, 0, {'name': 'Friday Morning', 'dayofweek': '4', 'hour_from': 8, 'hour_to': 12, 'day_period': 'morning'}),
                (0, 0, {'name': 'Friday Lunch', 'dayofweek': '4', 'hour_from': 12, 'hour_to': 13, 'day_period': 'lunch'}),
                (0, 0, {'name': 'Friday Evening', 'dayofweek': '4', 'hour_from': 13, 'hour_to': 16, 'day_period': 'afternoon'})
            ],
        })

        cls.calendar_35h_night = cls.env['resource.calendar'].create({
            'company_id': cls.company.id,
            'tz': "Europe/Brussels",
            'name': 'night calendar',
            'attendance_ids': [
                (0, 0, {'name': 'Monday Evening', 'dayofweek': '0', 'hour_from': 15, 'hour_to': 22, 'day_period': 'afternoon'}),
                (0, 0, {'name': 'Tuesday Evening', 'dayofweek': '1', 'hour_from': 15, 'hour_to': 22, 'day_period': 'afternoon'}),
                (0, 0, {'name': 'Wednesday Evening', 'dayofweek': '2', 'hour_from': 15, 'hour_to': 22, 'day_period': 'afternoon'}),
                (0, 0, {'name': 'Thursday Evening', 'dayofweek': '3', 'hour_from': 15, 'hour_to': 22, 'day_period': 'afternoon'}),
                (0, 0, {'name': 'Friday Evening', 'dayofweek': '4', 'hour_from': 15, 'hour_to': 22, 'day_period': 'afternoon'})
            ],
        })

        cls.partnerA = cls.env['res.partner'].create({
            'name': "Partner A"
        })
        cls.partnerB = cls.env['res.partner'].create({
            'name': "Partner B"
        })
        cls.partnerC = cls.env['res.partner'].create({
            'name': "Partner C"
        })
        cls.partnerD = cls.env['res.partner'].create({
            'name': "Partner D"
        })
        cls.employeeA = cls.env['hr.employee'].create({
            'name': "Partner A - Calendar 35h",
            'tz': "Europe/Brussels",
            'resource_calendar_id': cls.calendar_35h.id,
            'work_contact_id': cls.partnerA.id,
            })
        cls.employeeB = cls.env['hr.employee'].create({
            'name': "Partner B - Calendar 28h",
            'tz': "Europe/Brussels",
            'resource_calendar_id': cls.calendar_28h.id,
            'work_contact_id': cls.partnerB.id,
            })
        cls.employeeC = cls.env['hr.employee'].create({
            'name': "Partner C - Calendar 35h night",
            'tz': "Europe/Brussels",
            'resource_calendar_id': cls.calendar_35h_night.id,
            'work_contact_id': cls.partnerC.id,
        })
        cls.employeeD = cls.env['hr.employee'].create({
            'name': "Partner D - Calendar 35h No contract",
            'tz': "Europe/Brussels",
            'resource_calendar_id': cls.calendar_35h.id,
            'work_contact_id': cls.partnerD.id,
            })


from odoo.tests import common


class TestRelativeDateGranularity(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Model = cls.env['test_read_group.fill_temporal']
        cls.Model.create([{"value": "1", "date": "2021-02-09", "datetime": "2021-02-09 15:55:12"},
                          {"value": "20", "date": "2021-06-01", "datetime": "2021-06-01 16:55:14"},
                          {"value": "300", "date": "2022-02-01", "datetime": "2022-02-01 15:22:12"}])

    def test_full_usecase_month(self):
        result = self.Model.web_read_group(
            [], groupby=['date:month_number'], aggregates=['__count', 'value:sum'],
        )
        self.assertEqual(result, {
            'length': 2,
            'groups': [
                {
                    'date:month_number': 2,
                    '__count': 2,
                    'value:sum': 301,
                    '__domain_part': [('date.month_number', '=', 2)],
                }, {
                    'date:month_number': 6,
                    '__count': 1,
                    'value:sum': 20,
                    '__domain_part': [('date.month_number', '=', 6)],
                },
            ],
        })
        res = self.Model.search(result['groups'][0]['__domain_part'])
        self.assertEqual(len(res), 2)
        self.assertEqual(res.mapped('value'), [1, 300])

    def test_full_usecase_iso_week(self):
        result = self.Model.web_read_group(
            [], groupby=['date:iso_week_number'], aggregates=['__count', 'value:sum'])
        self.assertEqual(result, {
            'length': 3,
            'groups': [
                {
                    'date:iso_week_number': 5,
                    '__count': 1,
                    'value:sum': 300,
                    '__domain_part': [('date.iso_week_number', '=', 5)],
                }, {
                    'date:iso_week_number': 6,
                    '__count': 1,
                    'value:sum': 1,
                    '__domain_part': [('date.iso_week_number', '=', 6)],
                }, {
                    'date:iso_week_number': 22,
                    '__count': 1,
                    'value:sum': 20,
                    '__domain_part': [('date.iso_week_number', '=', 22)],
                },
            ],
        })
        res = self.Model.search(result['groups'][0]['__domain_part'])
        self.assertEqual(len(res), 1)
        self.assertEqual(res.mapped('value'), [300])

    def test_full_usecase_quarter(self):
        result = self.Model.web_read_group(
            [], groupby=['date:quarter_number'], aggregates=['__count', 'value:sum'],
        )
        self.assertEqual(result, {
            'length': 2,
            'groups': [
                {
                    'date:quarter_number': 1,
                    'value:sum': 301,
                    '__count': 2,
                    '__domain_part': [('date.quarter_number', '=', 1)],
                }, {
                    'date:quarter_number': 2,
                    'value:sum': 20,
                    '__count': 1,
                    '__domain_part': [('date.quarter_number', '=', 2)],
                },
            ],
        })
        res = self.Model.search(result['groups'][0]['__domain_part'])
        self.assertEqual(len(res), 2)
        self.assertEqual(res.mapped('value'), [1, 300])

    def test_full_usecase_year(self):
        result = self.Model.web_read_group(
            [], groupby=['date:year_number'], aggregates=['__count', 'value:sum'],
        )
        self.assertEqual(result, {
            'length': 2,
            'groups': [
                {
                    'date:year_number': 2021,
                    'value:sum': 21,
                    '__count': 2,
                    '__domain_part': [('date.year_number', '=', 2021)],
                }, {
                    'date:year_number': 2022,
                    'value:sum': 300,
                    '__count': 1,
                    '__domain_part': [('date.year_number', '=', 2022)],
                },
            ],
        })
        res = self.Model.search(result['groups'][0]['__domain_part'])
        self.assertEqual(len(res), 2)
        self.assertEqual(res.mapped('value'), [1, 20])

    def test_full_usecase_day_of_year(self):
        result = self.Model.web_read_group(
            [], groupby=['date:day_of_year'], aggregates=['__count', 'value:sum'],
        )
        self.assertEqual(result, {
            'length': 3,
            'groups': [
                {
                    'date:day_of_year': 32,
                    'value:sum': 300,
                    '__count': 1,
                    '__domain_part': [('date.day_of_year', '=', 32)],
                }, {
                    'date:day_of_year': 40,
                    'value:sum': 1,
                    '__count': 1,
                    '__domain_part': [('date.day_of_year', '=', 40)],
                }, {
                    'date:day_of_year': 152,
                    'value:sum': 20,
                    '__count': 1,
                    '__domain_part': [('date.day_of_year', '=', 152)],
                },
            ],
        })
        res = self.Model.search(result['groups'][0]['__domain_part'])
        self.assertEqual(len(res), 1)
        self.assertEqual(res.mapped('value'), [300])

    def test_full_usecase_day_of_month(self):
        result = self.Model.web_read_group(
            [], groupby=['date:day_of_month'], aggregates=['__count', 'value:sum'])
        self.assertEqual(result, {
            'length': 2,
            'groups': [
                {
                    'date:day_of_month': 1,
                    '__count': 2,
                    'value:sum': 320,
                    '__domain_part': [('date.day_of_month', '=', 1)],
                }, {
                    'date:day_of_month': 9,
                    '__count': 1,
                    'value:sum': 1,
                    '__domain_part': [('date.day_of_month', '=', 9)],
                },
            ],
        })
        res = self.Model.search(result['groups'][0]['__domain_part'])
        self.assertEqual(len(res), 2)
        self.assertEqual(res.mapped('value'), [20, 300])

    def test_full_usecase_day_of_week(self):
        result = self.Model.web_read_group(
            [], groupby=['date:day_of_week'], aggregates=['__count', 'value:sum'],
        )
        self.assertEqual(result, {
            'length': 1,
            'groups': [
                {
                    'date:day_of_week': 2,
                    '__count': 3,
                    'value:sum': 321,
                    '__domain_part': [('date.day_of_week', '=', 2)],
                },
            ],
        })
        res = self.Model.search(result['groups'][0]['__domain_part'])
        self.assertEqual(len(res), 3)
        self.assertEqual(res.mapped('value'), [1, 20, 300])

    def test_full_usecase_hour_number(self):
        result = self.Model.web_read_group(
            [], groupby=['datetime:hour_number'], aggregates=['__count', 'value:sum'],
        )
        self.assertEqual(result, result, {
            'length': 2,
            'groups': [
                {
                    'datetime:hour_number': 15,
                    '__count': 2,
                    'value:sum': 301,
                    '__domain_part': [('datetime.hour_number', '=', 15)],
                }, {
                    'datetime:hour_number': 16,
                    '__count': 1,
                    'value:sum': 20,
                    '__domain_part': [('datetime.hour_number', '=', 16)],
                },
            ],
        })
        res = self.Model.search(result['groups'][0]['__domain_part'])
        self.assertEqual(len(res), 2)
        self.assertEqual(res.mapped('value'), [1, 300])

    def test_full_usecase_minute_number(self):
        result = self.Model.web_read_group(
            [], groupby=['datetime:minute_number'], aggregates=['__count', 'value:sum'],
        )
        self.assertEqual(result, {
            'length': 2,
            'groups': [
                {
                    'datetime:minute_number': 22,
                    '__count': 1,
                    'value:sum': 300,
                    '__domain_part': [('datetime.minute_number', '=', 22)],
                }, {
                    'datetime:minute_number': 55,
                    '__count': 2,
                    'value:sum': 21,
                    '__domain_part': [('datetime.minute_number', '=', 55)],
                },
            ],
        })
        res = self.Model.search(result['groups'][0]['__domain_part'])
        self.assertEqual(len(res), 1)
        self.assertEqual(res.mapped('value'), [300])

    def test_full_usecase_second_number(self):
        result = self.Model.web_read_group(
            [], groupby=['datetime:second_number'], aggregates=['__count', 'value:sum'],
        )
        self.assertEqual(result, {
            'length': 2,
            'groups': [
                {
                    'datetime:second_number': 12,
                    '__count': 2,
                    'value:sum': 301,
                    '__domain_part': [('datetime.second_number', '=', 12)],
                }, {
                    'datetime:second_number': 14,
                    '__count': 1,
                    'value:sum': 20,
                    '__domain_part': [('datetime.second_number', '=', 14)],
                },
            ],
        })
        res = self.Model.search(result['groups'][0]['__domain_part'])
        self.assertEqual(len(res), 2)
        self.assertEqual(res.mapped('value'), [1, 300])


class TestRelativeDateGranularityWithTimezones(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        # execute a read_group with a relative granularity, it will give us back a domain
        # that contains the relative granularity to find the origin records. Use this domain
        # to find those records. This is exactly the way the pivot view behaves.
        super().setUpClass()
        cls.Model = cls.env['test_read_group.fill_temporal']
        cls.env['res.lang']._activate_lang('fr_BE')
        cls.env['res.lang']._activate_lang('NZ')

    def test_usecase_with_timezones(self):
        # Monday, it is the 5th week in UTC and the 6th in NZ
        self.Model.create({"value": "98", "datetime": "2023-02-05 23:55:00"})
        result = (self.Model.with_context({'tz': 'NZ'})  # GMT+12
                            .read_group([],
                                        fields=['datetime', 'value'],
                                        groupby=['datetime:iso_week_number']))
        self.assertEqual(result, [
                    {
                        'datetime:iso_week_number': 6,
                        'datetime_count': 1,
                        'value:sum': 98,
                        '__domain_part': [('datetime.iso_week_number', '=', 6)],
                    }])
        result = self.Model.with_context({'tz': 'NZ'}).search(result[0]['__domain_part'])
        self.assertEqual(len(result), 1)
        self.assertEqual(result.value, 98)

    def test_day_of_week_with_monday_as_first_day_of_week(self):
        self.Model.create({"value": "98", "date": "2023-02-05"})  # Sunday

        result = (self.Model.with_context({'tz': 'fr_BE'})  # GMT+1, first day of week is Monday
                  .read_group([],
                              fields=['date', 'value'],
                              groupby=['date:day_of_week']))
        self.assertEqual(result, [
            {
                'date:day_of_week': 6,
                '__count': 1,
                'value:sum': 98,
                '__domain_part': [('date.day_of_week', '=', 6)],
            }])
        res = self.Model.with_context({'tz': 'fr_BE'}).search(result[0]['__domain_part'])
        self.assertEqual(len(res), 1)
        self.assertEqual(res.mapped('value'), [98])

    def test_day_of_week_with_sunday_as_first_day_of_week(self):
        self.Model.create({"value": "98", "date": "2023-02-05"})  # Sunday

        result = (self.Model.with_context({'tz': 'NZ'})  # GMT+12, first day of week is Sunday
                  .read_group([],
                              fields=['date', 'value'],
                              groupby=['date:day_of_week']))
        self.assertEqual(result, [
            {
                'date:day_of_week': 0,
                '__count': 1,
                'value:sum': 98,
                '__domain_part': [('date.day_of_week', '=', 0)],
            }])

        res = self.Model.with_context({'tz': 'NZ'}).search(result[0]['__domain_part'])
        self.assertEqual(len(res), 1)
        self.assertEqual(res.mapped('value'), [98])

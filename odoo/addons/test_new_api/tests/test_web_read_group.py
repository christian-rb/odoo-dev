from odoo.tests.common import TransactionCase


class TestWebReadGroup(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tags = cls.env['test_new_api.multi.tag'].create([
            {'name': 'one'},
            {'name': 'two'},
            {'name': 'two'},
            {'name': 'there'},
            {'name': 'there'},
            {'name': 'there'},
        ])

    def test_web_read_group_limit_not_reached(self):
        result = self.env['test_new_api.multi.tag'].web_read_group(
            [], ['name'], ['__count'], limit=80,
        )
        self.assertEqual(result, {
            'groups': [
                {'name': 'one', '__count': 1, '__domain_part': [('name', '=', 'one')]},
                {'name': 'there', '__count': 3, '__domain_part': [('name', '=', 'there')]},
                {'name': 'two', '__count': 2, '__domain_part': [('name', '=', 'two')]},
            ],
            'length': 3,
        })

    def test_web_read_group_limit_reached(self):
        result = self.env['test_new_api.multi.tag'].web_read_group(
            [], ['name'], ['__count'], limit=2,
        )
        self.assertEqual(result, {
            'groups': [
                {'name': 'one', '__count': 1, '__domain_part': [('name', '=', 'one')]},
                {'name': 'there', '__count': 3, '__domain_part': [('name', '=', 'there')]},
            ],
            'length': 3,
        })

    def test_web_read_group_groupby_id(self):
        """ Test ['id'] as groupby, it is quite a dummy feature, but it should work """
        result = self.env['test_new_api.multi.tag'].web_read_group(
            [], ['id'], ['__count'], limit=2,
        )
        self.assertEqual(result, {
            'groups': [
                {'id': (self.tags[0].id, 'one'), '__count': 1, '__domain_part': [('id', '=', self.tags[0].id)]},
                {'id': (self.tags[1].id, 'two'), '__count': 1, '__domain_part': [('id', '=', self.tags[1].id)]},
            ],
            'length': 6,
        })

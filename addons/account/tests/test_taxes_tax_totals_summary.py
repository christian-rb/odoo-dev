from contextlib import contextmanager

from odoo.addons.account.tests.common import TestTaxCommon
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestTaxesTaxTotalsSummary(TestTaxCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.currency_id = cls.env.company.currency_id.id
        cls.tax_groups = cls.env['account.tax.group'].create([
            {'name': str(i), 'sequence': str(i)}
            for i in range(1, 6)
        ])

    @contextmanager
    def same_tax_group(self, taxes):
        taxes.tax_group_id = self.tax_groups[0]
        yield

    @contextmanager
    def different_tax_group(self, taxes):
        for i, tax in enumerate(taxes):
            tax.tax_group_id = self.tax_groups[i]
        yield

    def test_taxes_l10n_in(self):
        tests = []
        tax1 = self.percent_tax(6, include_base_amount=True)
        tax2 = self.percent_tax(6, include_base_amount=True, is_base_affected=False)
        tax3 = self.percent_tax(3)
        taxes = tax1 + tax2 + tax3

        with self.same_tax_group(taxes):
            tests.extend([
                self._prepare_tax_totals_summary_test(
                    self._prepare_document_params(rounding_method='round_per_line'),
                    [
                        self._prepare_document_line_params(15.89, taxes=taxes),
                        self._prepare_document_line_params(15.89, taxes=taxes),
                    ],
                    {
                        'same_tax_base': True,
                        'currency_id': self.currency_id,
                        'untaxed_amount': 31.78,
                        'tax_amount': 4.86,
                        'total_amount': 36.64,
                        'subtotals': [
                            {
                                'name': "Untaxed Amount",
                                'base': 31.78,
                                'tax_amount': 4.86,
                                'tax_groups': [
                                    {
                                        'id': self.tax_groups[0].id,
                                        'base': 31.78,
                                        'tax_amount': 4.86,
                                        'display_base': 31.78,
                                        'group_name': self.tax_groups[0].name,
                                    },
                                ],
                            },
                        ],
                    },
                ),
                self._prepare_tax_totals_summary_test(
                    self._prepare_document_params(rounding_method='round_globally'),
                    [
                        self._prepare_document_line_params(15.89, taxes=taxes),
                        self._prepare_document_line_params(15.89, taxes=taxes),
                    ],
                    {
                        'same_tax_base': True,
                        'currency_id': self.currency_id,
                        'untaxed_amount': 31.78,
                        'tax_amount': 4.890000000000001,
                        'total_amount': 36.67,
                        'subtotals': [
                            {
                                'name': "Untaxed Amount",
                                'base': 31.78,
                                'tax_amount': 4.890000000000001,
                                'tax_groups': [
                                    {
                                        'id': self.tax_groups[0].id,
                                        'base': 31.78,
                                        'tax_amount': 4.890000000000001,
                                        'display_base': 31.78,
                                        'group_name': self.tax_groups[0].name,
                                    },
                                ],
                            },
                        ],
                    },
                ),
            ])

        with self.different_tax_group(taxes):
            tests.extend([
                self._prepare_total_per_tax_summary_test(
                    self._prepare_document_params(rounding_method='round_per_line'),
                    [
                        self._prepare_document_line_params(15.89, taxes=taxes),
                        self._prepare_document_line_params(15.89, taxes=taxes),
                    ],
                    {
                        'untaxed_amount': 31.78,
                        'tax_amount': 4.86,
                        'total_amount': 36.64,
                        'subtotals': {
                            tax1.id: {
                                'base': 31.78,
                                'tax_amount': 1.9000000000000001,
                                'display_base': 31.78,
                            },
                            tax2.id: {
                                'base': 31.78,
                                'tax_amount': 1.9000000000000001,
                                'display_base': 31.78,
                            },
                            tax3.id: {
                                'base': 35.58,
                                'tax_amount': 1.06,
                                'display_base': 35.58,
                            },
                        },
                    },
                ),
                self._prepare_tax_totals_summary_test(
                    self._prepare_document_params(rounding_method='round_per_line'),
                    [
                        self._prepare_document_line_params(15.89, taxes=taxes),
                        self._prepare_document_line_params(15.89, taxes=taxes),
                    ],
                    {
                        'same_tax_base': False,
                        'currency_id': self.currency_id,
                        'untaxed_amount': 31.78,
                        'tax_amount': 4.86,
                        'total_amount': 36.64,
                        'subtotals': [
                            {
                                'name': "Untaxed Amount",
                                'base': 31.78,
                                'tax_amount': 4.86,
                                'tax_groups': [
                                    {
                                        'id': self.tax_groups[0].id,
                                        'base': 31.78,
                                        'tax_amount': 1.9000000000000001,
                                        'display_base': 31.78,
                                        'group_name': self.tax_groups[0].name,
                                    },
                                    {
                                        'id': self.tax_groups[1].id,
                                        'base': 31.78,
                                        'tax_amount': 1.9000000000000001,
                                        'display_base': 31.78,
                                        'group_name': self.tax_groups[1].name,
                                    },
                                    {
                                        'id': self.tax_groups[2].id,
                                        'base': 35.58,
                                        'tax_amount': 1.06,
                                        'display_base': 35.58,
                                        'group_name': self.tax_groups[2].name,
                                    },
                                ],
                            },
                        ],
                    },
                ),
                self._prepare_total_per_tax_summary_test(
                    self._prepare_document_params(rounding_method='round_globally'),
                    [
                        self._prepare_document_line_params(15.89, taxes=taxes),
                        self._prepare_document_line_params(15.89, taxes=taxes),
                    ],
                    {
                        'untaxed_amount': 31.78,
                        'tax_amount': 4.890000000000001,
                        'total_amount': 36.67,
                        'subtotals': {
                            tax1.id: {
                                'base': 31.78,
                                'tax_amount': 1.9100000000000001,
                                'display_base': 31.78,
                            },
                            tax2.id: {
                                'base': 31.78,
                                'tax_amount': 1.9100000000000001,
                                'display_base': 31.78,
                            },
                            tax3.id: {
                                'base': 35.59,
                                'tax_amount': 1.07,
                                'display_base': 35.59,
                            },
                        },
                    },
                ),
                self._prepare_tax_totals_summary_test(
                    self._prepare_document_params(rounding_method='round_globally'),
                    [
                        self._prepare_document_line_params(15.89, taxes=taxes),
                        self._prepare_document_line_params(15.89, taxes=taxes),
                    ],
                    {
                        'same_tax_base': False,
                        'currency_id': self.currency_id,
                        'untaxed_amount': 31.78,
                        'tax_amount': 4.890000000000001,
                        'total_amount': 36.67,
                        'subtotals': [
                            {
                                'name': "Untaxed Amount",
                                'base': 31.78,
                                'tax_amount': 4.890000000000001,
                                'tax_groups': [
                                    {
                                        'id': self.tax_groups[0].id,
                                        'base': 31.78,
                                        'tax_amount': 1.9100000000000001,
                                        'display_base': 31.78,
                                        'group_name': self.tax_groups[0].name,
                                    },
                                    {
                                        'id': self.tax_groups[1].id,
                                        'base': 31.78,
                                        'tax_amount': 1.9100000000000001,
                                        'display_base': 31.78,
                                        'group_name': self.tax_groups[1].name,
                                    },
                                    {
                                        'id': self.tax_groups[2].id,
                                        'base': 35.59,
                                        'tax_amount': 1.07,
                                        'display_base': 35.59,
                                        'group_name': self.tax_groups[2].name,
                                    },
                                ],
                            },
                        ],
                    },
                ),
            ])

        tax1.price_include = True
        tax2.price_include = True
        with self.same_tax_group(taxes):
            tests.extend([
                self._prepare_tax_totals_summary_test(
                    self._prepare_document_params(rounding_method='round_per_line'),
                    [
                        self._prepare_document_line_params(17.79, taxes=taxes),
                        self._prepare_document_line_params(17.79, taxes=taxes),
                    ],
                    {
                        'same_tax_base': True,
                        'currency_id': self.currency_id,
                        'untaxed_amount': 31.78,
                        'tax_amount': 4.86,
                        'total_amount': 36.64,
                        'subtotals': [
                            {
                                'name': "Untaxed Amount",
                                'base': 31.78,
                                'tax_amount': 4.86,
                                'tax_groups': [
                                    {
                                        'id': self.tax_groups[0].id,
                                        'base': 31.78,
                                        'tax_amount': 4.86,
                                        'display_base': 31.78,
                                        'group_name': self.tax_groups[0].name,
                                    },
                                ],
                            },
                        ],
                    },
                ),
                self._prepare_tax_totals_summary_test(
                    self._prepare_document_params(rounding_method='round_globally'),
                    [
                        self._prepare_document_line_params(17.79, taxes=taxes),
                        self._prepare_document_line_params(17.79, taxes=taxes),
                    ],
                    {
                        'same_tax_base': True,
                        'currency_id': self.currency_id,
                        'untaxed_amount': 31.76,
                        'tax_amount': 4.890000000000001,
                        'total_amount': 36.650000000000006,
                        'subtotals': [
                            {
                                'name': "Untaxed Amount",
                                'base': 31.76,
                                'tax_amount': 4.890000000000001,
                                'tax_groups': [
                                    {
                                        'id': self.tax_groups[0].id,
                                        'base': 31.76,
                                        'tax_amount': 4.890000000000001,
                                        'display_base': 31.76,
                                        'group_name': self.tax_groups[0].name,
                                    },
                                ],
                            },
                        ],
                    },
                ),
            ])

        with self.different_tax_group(taxes):
            tests.extend([
                self._prepare_total_per_tax_summary_test(
                    self._prepare_document_params(rounding_method='round_per_line'),
                    [
                        self._prepare_document_line_params(17.79, taxes=taxes),
                        self._prepare_document_line_params(17.79, taxes=taxes),
                    ],
                    {
                        'untaxed_amount': 31.78,
                        'tax_amount': 4.86,
                        'total_amount': 36.64,
                        'subtotals': {
                            tax1.id: {
                                'base': 31.78,
                                'tax_amount': 1.9000000000000001,
                                'display_base': 31.78,
                            },
                            tax2.id: {
                                'base': 31.78,
                                'tax_amount': 1.9000000000000001,
                                'display_base': 31.78,
                            },
                            tax3.id: {
                                'base': 35.58,
                                'tax_amount': 1.06,
                                'display_base': 35.58,
                            },
                        },
                    },
                ),
                self._prepare_tax_totals_summary_test(
                    self._prepare_document_params(rounding_method='round_per_line'),
                    [
                        self._prepare_document_line_params(17.79, taxes=taxes),
                        self._prepare_document_line_params(17.79, taxes=taxes),
                    ],
                    {
                        'same_tax_base': False,
                        'currency_id': self.currency_id,
                        'untaxed_amount': 31.78,
                        'tax_amount': 4.86,
                        'total_amount': 36.64,
                        'subtotals': [
                            {
                                'name': "Untaxed Amount",
                                'base': 31.78,
                                'tax_amount': 4.86,
                                'tax_groups': [
                                    {
                                        'id': self.tax_groups[0].id,
                                        'base': 31.78,
                                        'tax_amount': 1.9000000000000001,
                                        'display_base': 31.78,
                                        'group_name': self.tax_groups[0].name,
                                    },
                                    {
                                        'id': self.tax_groups[1].id,
                                        'base': 31.78,
                                        'tax_amount': 1.9000000000000001,
                                        'display_base': 31.78,
                                        'group_name': self.tax_groups[1].name,
                                    },
                                    {
                                        'id': self.tax_groups[2].id,
                                        'base': 35.58,
                                        'tax_amount': 1.06,
                                        'display_base': 35.58,
                                        'group_name': self.tax_groups[2].name,
                                    },
                                ],
                            },
                        ],
                    },
                ),
                self._prepare_total_per_tax_summary_test(
                    self._prepare_document_params(rounding_method='round_globally'),
                    [
                        self._prepare_document_line_params(17.79, taxes=taxes),
                        self._prepare_document_line_params(17.79, taxes=taxes),
                    ],
                    {
                        'untaxed_amount': 31.76,
                        'tax_amount': 4.890000000000001,
                        'total_amount': 36.650000000000006,
                        'subtotals': {
                            tax1.id: {
                                'base': 31.76,
                                'tax_amount': 1.9100000000000001,
                                'display_base': 31.76,
                            },
                            tax2.id: {
                                'base': 31.76,
                                'tax_amount': 1.9100000000000001,
                                'display_base': 31.76,
                            },
                            tax3.id: {
                                'base': 35.58,
                                'tax_amount': 1.07,
                                'display_base': 35.58,
                            },
                        },
                    },
                ),
                self._prepare_tax_totals_summary_test(
                    self._prepare_document_params(rounding_method='round_globally'),
                    [
                        self._prepare_document_line_params(17.79, taxes=taxes),
                        self._prepare_document_line_params(17.79, taxes=taxes),
                    ],
                    {
                        'same_tax_base': False,
                        'currency_id': self.currency_id,
                        'untaxed_amount': 31.76,
                        'tax_amount': 4.890000000000001,
                        'total_amount': 36.650000000000006,
                        'subtotals': [
                            {
                                'name': "Untaxed Amount",
                                'base': 31.76,
                                'tax_amount': 4.890000000000001,
                                'tax_groups': [
                                    {
                                        'id': self.tax_groups[0].id,
                                        'base': 31.76,
                                        'tax_amount': 1.9100000000000001,
                                        'display_base': 31.76,
                                        'group_name': self.tax_groups[0].name,
                                    },
                                    {
                                        'id': self.tax_groups[1].id,
                                        'base': 31.76,
                                        'tax_amount': 1.9100000000000001,
                                        'display_base': 31.76,
                                        'group_name': self.tax_groups[1].name,
                                    },
                                    {
                                        'id': self.tax_groups[2].id,
                                        'base': 35.58,
                                        'tax_amount': 1.07,
                                        'display_base': 35.58,
                                        'group_name': self.tax_groups[2].name,
                                    },
                                ],
                            },
                        ],
                    },
                ),
            ])
        self._assert_tests(tests, mode='py')

    def test_taxes_l10n_br(self):
        tests = []
        tax1 = self.division_tax(5)
        tax2 = self.division_tax(3)
        tax3 = self.division_tax(0.65)
        tax4 = self.division_tax(9)
        tax5 = self.division_tax(15)
        taxes = tax1 + tax2 + tax3 + tax4 + tax5

        with self.same_tax_group(taxes):
            for rounding_method in ('round_per_line', 'round_globally'):
                tests.append(
                    self._prepare_tax_totals_summary_test(
                        self._prepare_document_params(rounding_method=rounding_method),
                        [
                            self._prepare_document_line_params(32.33, taxes=taxes),
                            self._prepare_document_line_params(32.33, taxes=taxes),
                        ],
                        {
                            'same_tax_base': True,
                            'currency_id': self.currency_id,
                            'untaxed_amount': 64.66,
                            'tax_amount': 31.339999999999996,
                            'total_amount': 96.0,
                            'subtotals': [
                                {
                                    'name': "Untaxed Amount",
                                    'base': 64.66,
                                    'tax_amount': 31.339999999999996,
                                    'tax_groups': [
                                        {
                                            'id': self.tax_groups[0].id,
                                            'base': 64.66,
                                            'tax_amount': 31.339999999999996,
                                            'display_base': 64.66,
                                            'group_name': self.tax_groups[0].name,
                                        },
                                    ],
                                },
                            ],
                        },
                    ),
                )

        with self.different_tax_group(taxes):
            for rounding_method in ('round_per_line', 'round_globally'):
                tests.extend([
                    self._prepare_total_per_tax_summary_test(
                        self._prepare_document_params(rounding_method=rounding_method),
                        [
                            self._prepare_document_line_params(32.33, taxes=taxes),
                            self._prepare_document_line_params(32.33, taxes=taxes),
                        ],
                        {
                            'untaxed_amount': 64.66,
                            'tax_amount': 31.339999999999996,
                            'total_amount': 96.0,
                            'subtotals': {
                                tax1.id: {
                                    'base': 64.66,
                                    'tax_amount': 4.8,
                                    'display_base': 64.66,
                                },
                                tax2.id: {
                                    'base': 64.66,
                                    'tax_amount': 2.88,
                                    'display_base': 64.66,
                                },
                                tax3.id: {
                                    'base': 64.66,
                                    'tax_amount': 0.62,
                                    'display_base': 64.66,
                                },
                                tax4.id: {
                                    'base': 64.66,
                                    'tax_amount': 8.64,
                                    'display_base': 64.66,
                                },
                                tax5.id: {
                                    'base': 64.66,
                                    'tax_amount': 14.4,
                                    'display_base': 64.66,
                                },
                            },
                        },
                    ),
                    self._prepare_tax_totals_summary_test(
                        self._prepare_document_params(rounding_method=rounding_method),
                        [
                            self._prepare_document_line_params(32.33, taxes=taxes),
                            self._prepare_document_line_params(32.33, taxes=taxes),
                        ],
                        {
                            'same_tax_base': True,
                            'currency_id': self.currency_id,
                            'untaxed_amount': 64.66,
                            'tax_amount': 31.339999999999996,
                            'total_amount': 96.0,
                            'subtotals': [
                                {
                                    'name': "Untaxed Amount",
                                    'base': 64.66,
                                    'tax_amount': 31.339999999999996,
                                    'tax_groups': [
                                        {
                                            'id': self.tax_groups[0].id,
                                            'base': 64.66,
                                            'tax_amount': 4.8,
                                            'display_base': 64.66,
                                            'group_name': self.tax_groups[0].name,
                                        },
                                        {
                                            'id': self.tax_groups[1].id,
                                            'base': 64.66,
                                            'tax_amount': 2.88,
                                            'display_base': 64.66,
                                            'group_name': self.tax_groups[1].name,
                                        },
                                        {
                                            'id': self.tax_groups[2].id,
                                            'base': 64.66,
                                            'tax_amount': 0.62,
                                            'display_base': 64.66,
                                            'group_name': self.tax_groups[2].name,
                                        },
                                        {
                                            'id': self.tax_groups[3].id,
                                            'base': 64.66,
                                            'tax_amount': 8.64,
                                            'display_base': 64.66,
                                            'group_name': self.tax_groups[3].name,
                                        },
                                        {
                                            'id': self.tax_groups[4].id,
                                            'base': 64.66,
                                            'tax_amount': 14.4,
                                            'display_base': 64.66,
                                            'group_name': self.tax_groups[4].name,
                                        },
                                    ],
                                },
                            ],
                        },
                    )
                ])

        taxes.price_include = True
        with self.same_tax_group(taxes):
            for rounding_method in ('round_per_line', 'round_globally'):
                tests.append(
                    self._prepare_tax_totals_summary_test(
                        self._prepare_document_params(rounding_method=rounding_method),
                        [
                            self._prepare_document_line_params(48.0, taxes=taxes),
                            self._prepare_document_line_params(48.0, taxes=taxes),
                        ],
                        {
                            'same_tax_base': True,
                            'currency_id': self.currency_id,
                            'untaxed_amount': 64.66,
                            'tax_amount': 31.339999999999996,
                            'total_amount': 96.0,
                            'subtotals': [
                                {
                                    'name': "Untaxed Amount",
                                    'base': 64.66,
                                    'tax_amount': 31.339999999999996,
                                    'tax_groups': [
                                        {
                                            'id': self.tax_groups[0].id,
                                            'base': 64.66,
                                            'tax_amount': 31.339999999999996,
                                            'display_base': 96.0,
                                            'group_name': self.tax_groups[0].name,
                                        },
                                    ],
                                },
                            ],
                        },
                    ),
                )

        with self.different_tax_group(taxes):
            for rounding_method in ('round_per_line', 'round_globally'):
                tests.extend([
                    self._prepare_total_per_tax_summary_test(
                        self._prepare_document_params(rounding_method=rounding_method),
                        [
                            self._prepare_document_line_params(48.0, taxes=taxes),
                            self._prepare_document_line_params(48.0, taxes=taxes),
                        ],
                        {
                            'untaxed_amount': 64.66,
                            'tax_amount': 31.339999999999996,
                            'total_amount': 96.0,
                            'subtotals': {
                                tax1.id: {
                                    'base': 64.66,
                                    'tax_amount': 4.8,
                                    'display_base': 96.0,
                                },
                                tax2.id: {
                                    'base': 64.66,
                                    'tax_amount': 2.88,
                                    'display_base': 96.0,
                                },
                                tax3.id: {
                                    'base': 64.66,
                                    'tax_amount': 0.62,
                                    'display_base': 96.0,
                                },
                                tax4.id: {
                                    'base': 64.66,
                                    'tax_amount': 8.64,
                                    'display_base': 96.0,
                                },
                                tax5.id: {
                                    'base': 64.66,
                                    'tax_amount': 14.4,
                                    'display_base': 96.0,
                                },
                            },
                        },
                    ),
                    self._prepare_tax_totals_summary_test(
                        self._prepare_document_params(rounding_method=rounding_method),
                        [
                            self._prepare_document_line_params(48.0, taxes=taxes),
                            self._prepare_document_line_params(48.0, taxes=taxes),
                        ],
                        {
                            'same_tax_base': True,
                            'currency_id': self.currency_id,
                            'untaxed_amount': 64.66,
                            'tax_amount': 31.339999999999996,
                            'total_amount': 96.0,
                            'subtotals': [
                                {
                                    'name': "Untaxed Amount",
                                    'base': 64.66,
                                    'tax_amount': 31.339999999999996,
                                    'tax_groups': [
                                        {
                                            'id': self.tax_groups[0].id,
                                            'base': 64.66,
                                            'tax_amount': 4.8,
                                            'display_base': 96.0,
                                            'group_name': self.tax_groups[0].name,
                                        },
                                        {
                                            'id': self.tax_groups[1].id,
                                            'base': 64.66,
                                            'tax_amount': 2.88,
                                            'display_base': 96.0,
                                            'group_name': self.tax_groups[1].name,
                                        },
                                        {
                                            'id': self.tax_groups[2].id,
                                            'base': 64.66,
                                            'tax_amount': 0.62,
                                            'display_base': 96.0,
                                            'group_name': self.tax_groups[2].name,
                                        },
                                        {
                                            'id': self.tax_groups[3].id,
                                            'base': 64.66,
                                            'tax_amount': 8.64,
                                            'display_base': 96.0,
                                            'group_name': self.tax_groups[3].name,
                                        },
                                        {
                                            'id': self.tax_groups[4].id,
                                            'base': 64.66,
                                            'tax_amount': 14.4,
                                            'display_base': 96.0,
                                            'group_name': self.tax_groups[4].name,
                                        },
                                    ],
                                },
                            ],
                        },
                    )
                ])
        self._assert_tests(tests, mode='py')

    def test_taxes_l10n_be(self):
        tests = []
        tax1 = self.fixed_tax(1, include_base_amount=True)
        tax2 = self.percent_tax(21)
        taxes = tax1 + tax2

        with self.same_tax_group(taxes):
            tests.extend([
                self._prepare_tax_totals_summary_test(
                    self._prepare_document_params(rounding_method='round_per_line'),
                    [
                        self._prepare_document_line_params(16.79, taxes=taxes),
                        self._prepare_document_line_params(16.79, taxes=taxes),
                    ],
                    {
                        'same_tax_base': True,
                        'currency_id': self.currency_id,
                        'untaxed_amount': 33.58,
                        'tax_amount': 9.48,
                        'total_amount': 43.06,
                        'subtotals': [
                            {
                                'name': "Untaxed Amount",
                                'base': 33.58,
                                'tax_amount': 9.48,
                                'tax_groups': [
                                    {
                                        'id': self.tax_groups[0].id,
                                        'base': 33.58,
                                        'tax_amount': 9.48,
                                        'display_base': 33.58,
                                        'group_name': self.tax_groups[0].name,
                                    },
                                ],
                            },
                        ],
                    },
                ),
                self._prepare_tax_totals_summary_test(
                    self._prepare_document_params(rounding_method='round_globally'),
                    [
                        self._prepare_document_line_params(16.79, taxes=taxes),
                        self._prepare_document_line_params(16.79, taxes=taxes),
                    ],
                    {
                        'same_tax_base': True,
                        'currency_id': self.currency_id,
                        'untaxed_amount': 33.58,
                        'tax_amount': 9.469999999999999,
                        'total_amount': 43.05,
                        'subtotals': [
                            {
                                'name': "Untaxed Amount",
                                'base': 33.58,
                                'tax_amount': 9.469999999999999,
                                'tax_groups': [
                                    {
                                        'id': self.tax_groups[0].id,
                                        'base': 33.58,
                                        'tax_amount': 9.469999999999999,
                                        'display_base': 33.58,
                                        'group_name': self.tax_groups[0].name,
                                    },
                                ],
                            },
                        ],
                    },
                ),
            ])

        with self.different_tax_group(taxes):
            tests.extend([
                self._prepare_total_per_tax_summary_test(
                    self._prepare_document_params(rounding_method='round_per_line'),
                    [
                        self._prepare_document_line_params(16.79, taxes=taxes),
                        self._prepare_document_line_params(16.79, taxes=taxes),
                    ],
                    {
                        'untaxed_amount': 33.58,
                        'tax_amount': 9.48,
                        'total_amount': 43.06,
                        'subtotals': {
                            tax1.id: {
                                'base': 33.58,
                                'tax_amount': 2.0,
                                'display_base': None,
                            },
                            tax2.id: {
                                'base': 35.58,
                                'tax_amount': 7.48,
                                'display_base': 35.58,
                            },
                        },
                    },
                ),
                self._prepare_tax_totals_summary_test(
                    self._prepare_document_params(rounding_method='round_per_line'),
                    [
                        self._prepare_document_line_params(16.79, taxes=taxes),
                        self._prepare_document_line_params(16.79, taxes=taxes),
                    ],
                    {
                        'same_tax_base': True,
                        'currency_id': self.currency_id,
                        'untaxed_amount': 33.58,
                        'tax_amount': 9.48,
                        'total_amount': 43.06,
                        'subtotals': [
                            {
                                'name': "Untaxed Amount",
                                'base': 33.58,
                                'tax_amount': 9.48,
                                'tax_groups': [
                                    {
                                        'id': self.tax_groups[0].id,
                                        'base': 33.58,
                                        'tax_amount': 2.0,
                                        'display_base': None,
                                        'group_name': self.tax_groups[0].name,
                                    },
                                    {
                                        'id': self.tax_groups[1].id,
                                        'base': 35.58,
                                        'tax_amount': 7.48,
                                        'display_base': 35.58,
                                        'group_name': self.tax_groups[1].name,
                                    },
                                ],
                            },
                        ],
                    },
                ),
                self._prepare_total_per_tax_summary_test(
                    self._prepare_document_params(rounding_method='round_globally'),
                    [
                        self._prepare_document_line_params(16.79, taxes=taxes),
                        self._prepare_document_line_params(16.79, taxes=taxes),
                    ],
                    {
                        'untaxed_amount': 33.58,
                        'tax_amount': 9.469999999999999,
                        'total_amount': 43.05,
                        'subtotals': {
                            tax1.id: {
                                'base': 33.58,
                                'tax_amount': 2.0,
                                'display_base': None,
                            },
                            tax2.id: {
                                'base': 35.58,
                                'tax_amount': 7.47,
                                'display_base': 35.58,
                            },
                        },
                    },
                ),
                self._prepare_tax_totals_summary_test(
                    self._prepare_document_params(rounding_method='round_globally'),
                    [
                        self._prepare_document_line_params(16.79, taxes=taxes),
                        self._prepare_document_line_params(16.79, taxes=taxes),
                    ],
                    {
                        'same_tax_base': True,
                        'currency_id': self.currency_id,
                        'untaxed_amount': 33.58,
                        'tax_amount': 9.469999999999999,
                        'total_amount': 43.05,
                        'subtotals': [
                            {
                                'name': "Untaxed Amount",
                                'base': 33.58,
                                'tax_amount': 9.469999999999999,
                                'tax_groups': [
                                    {
                                        'id': self.tax_groups[0].id,
                                        'base': 33.58,
                                        'tax_amount': 2.0,
                                        'display_base': None,
                                        'group_name': self.tax_groups[0].name,
                                    },
                                    {
                                        'id': self.tax_groups[1].id,
                                        'base': 35.58,
                                        'tax_amount': 7.47,
                                        'display_base': 35.58,
                                        'group_name': self.tax_groups[1].name,
                                    },
                                ],
                            },
                        ],
                    },
                ),
            ])

        taxes.price_include = True
        with self.same_tax_group(taxes):
            tests.extend([
                self._prepare_tax_totals_summary_test(
                    self._prepare_document_params(rounding_method='round_per_line'),
                    [
                        self._prepare_document_line_params(21.53, taxes=taxes),
                        self._prepare_document_line_params(21.53, taxes=taxes),
                    ],
                    {
                        'same_tax_base': True,
                        'currency_id': self.currency_id,
                        'untaxed_amount': 33.58,
                        'tax_amount': 9.48,
                        'total_amount': 43.06,
                        'subtotals': [
                            {
                                'name': "Untaxed Amount",
                                'base': 33.58,
                                'tax_amount': 9.48,
                                'tax_groups': [
                                    {
                                        'id': self.tax_groups[0].id,
                                        'base': 33.58,
                                        'tax_amount': 9.48,
                                        'display_base': 33.58,
                                        'group_name': self.tax_groups[0].name,
                                    },
                                ],
                            },
                        ],
                    },
                ),
                self._prepare_tax_totals_summary_test(
                    self._prepare_document_params(rounding_method='round_globally'),
                    [
                        self._prepare_document_line_params(21.53, taxes=taxes),
                        self._prepare_document_line_params(21.53, taxes=taxes),
                    ],
                    {
                        'same_tax_base': True,
                        'currency_id': self.currency_id,
                        'untaxed_amount': 33.58,
                        'tax_amount': 9.469999999999999,
                        'total_amount': 43.05,
                        'subtotals': [
                            {
                                'name': "Untaxed Amount",
                                'base': 33.58,
                                'tax_amount': 9.469999999999999,
                                'tax_groups': [
                                    {
                                        'id': self.tax_groups[0].id,
                                        'base': 33.59,
                                        'tax_amount': 9.469999999999999,
                                        'display_base': 33.59,
                                        'group_name': self.tax_groups[0].name,
                                    },
                                ],
                            },
                        ],
                    },
                ),
            ])

        with self.different_tax_group(taxes):
            tests.extend([
                self._prepare_total_per_tax_summary_test(
                    self._prepare_document_params(rounding_method='round_per_line'),
                    [
                        self._prepare_document_line_params(21.53, taxes=taxes),
                        self._prepare_document_line_params(21.53, taxes=taxes),
                    ],
                    {
                        'untaxed_amount': 33.58,
                        'tax_amount': 9.48,
                        'total_amount': 43.06,
                        'subtotals': {
                            tax1.id: {
                                'base': 33.58,
                                'tax_amount': 2.0,
                                'display_base': None,
                            },
                            tax2.id: {
                                'base': 35.58,
                                'tax_amount': 7.48,
                                'display_base': 35.58,
                            },
                        },
                    },
                ),
                self._prepare_tax_totals_summary_test(
                    self._prepare_document_params(rounding_method='round_per_line'),
                    [
                        self._prepare_document_line_params(21.53, taxes=taxes),
                        self._prepare_document_line_params(21.53, taxes=taxes),
                    ],
                    {
                        'same_tax_base': True,
                        'currency_id': self.currency_id,
                        'untaxed_amount': 33.58,
                        'tax_amount': 9.48,
                        'total_amount': 43.06,
                        'subtotals': [
                            {
                                'name': "Untaxed Amount",
                                'base': 33.58,
                                'tax_amount': 9.48,
                                'tax_groups': [
                                    {
                                        'id': self.tax_groups[0].id,
                                        'base': 33.58,
                                        'tax_amount': 2.0,
                                        'display_base': None,
                                        'group_name': self.tax_groups[0].name,
                                    },
                                    {
                                        'id': self.tax_groups[1].id,
                                        'base': 35.58,
                                        'tax_amount': 7.48,
                                        'display_base': 35.58,
                                        'group_name': self.tax_groups[1].name,
                                    },
                                ],
                            },
                        ],
                    },
                ),
                self._prepare_total_per_tax_summary_test(
                    self._prepare_document_params(rounding_method='round_globally'),
                    [
                        self._prepare_document_line_params(21.53, taxes=taxes),
                        self._prepare_document_line_params(21.53, taxes=taxes),
                    ],
                    {
                        'untaxed_amount': 33.58,
                        'tax_amount': 9.469999999999999,
                        'total_amount': 43.05,
                        'subtotals': {
                            tax1.id: {
                                'base': 33.59,
                                'tax_amount': 2.0,
                                'display_base': None,
                            },
                            tax2.id: {
                                'base': 35.59,
                                'tax_amount': 7.47,
                                'display_base': 35.59,
                            },
                        },
                    },
                ),
                self._prepare_tax_totals_summary_test(
                    self._prepare_document_params(rounding_method='round_globally'),
                    [
                        self._prepare_document_line_params(21.53, taxes=taxes),
                        self._prepare_document_line_params(21.53, taxes=taxes),
                    ],
                    {
                        'same_tax_base': True,
                        'currency_id': self.currency_id,
                        'untaxed_amount': 33.58,
                        'tax_amount': 9.469999999999999,
                        'total_amount': 43.05,
                        'subtotals': [
                            {
                                'name': "Untaxed Amount",
                                'base': 33.58,
                                'tax_amount': 9.469999999999999,
                                'tax_groups': [
                                    {
                                        'id': self.tax_groups[0].id,
                                        'base': 33.59,
                                        'tax_amount': 2.0,
                                        'display_base': None,
                                        'group_name': self.tax_groups[0].name,
                                    },
                                    {
                                        'id': self.tax_groups[1].id,
                                        'base': 35.59,
                                        'tax_amount': 7.47,
                                        'display_base': 35.59,
                                        'group_name': self.tax_groups[1].name,
                                    },
                                ],
                            },
                        ],
                    },
                ),
            ])
        self._assert_tests(tests, mode='py')

    def test_cash_rounding(self):
        tax1 = self.division_tax(5, tax_group_id=self.tax_groups[0].id)
        tax2 = self.division_tax(3, tax_group_id=self.tax_groups[1].id)
        tax3 = self.division_tax(0.65, tax_group_id=self.tax_groups[2].id)
        tax4 = self.division_tax(9, tax_group_id=self.tax_groups[3].id)
        tax5 = self.division_tax(15, tax_group_id=self.tax_groups[4].id)
        taxes = tax1 + tax2 + tax3 + tax4 + tax5

        tests = [
            self._prepare_tax_totals_summary_test(
                self._prepare_document_params(rounding_method='round_per_line'),
                [
                    self._prepare_document_cash_rounding('add_invoice_line'),
                    self._prepare_document_line_params(32.4, taxes=taxes),
                ],
                {
                    'same_tax_base': True,
                    'currency_id': self.currency_id,
                    'untaxed_amount': 32.39,
                    'cash_rounding_amount': -0.01,
                    'tax_amount': 15.71,
                    'total_amount': 48.1,
                    'subtotals': [
                        {
                            'name': "Untaxed Amount",
                            'base': 32.4,
                            'tax_amount': 15.71,
                            'tax_groups': [
                                {
                                    'id': self.tax_groups[0].id,
                                    'base': 32.4,
                                    'tax_amount': 2.41,
                                    'display_base': 32.4,
                                    'group_name': self.tax_groups[0].name,
                                },
                                {
                                    'id': self.tax_groups[1].id,
                                    'base': 32.4,
                                    'tax_amount': 1.44,
                                    'display_base': 32.4,
                                    'group_name': self.tax_groups[1].name,
                                },
                                {
                                    'id': self.tax_groups[2].id,
                                    'base': 32.4,
                                    'tax_amount': 0.31,
                                    'display_base': 32.4,
                                    'group_name': self.tax_groups[2].name,
                                },
                                {
                                    'id': self.tax_groups[3].id,
                                    'base': 32.4,
                                    'tax_amount': 4.33,
                                    'display_base': 32.4,
                                    'group_name': self.tax_groups[3].name,
                                },
                                {
                                    'id': self.tax_groups[4].id,
                                    'base': 32.4,
                                    'tax_amount': 7.22,
                                    'display_base': 32.4,
                                    'group_name': self.tax_groups[4].name,
                                },
                            ],
                        },
                    ],
                },
            ),
            self._prepare_tax_totals_summary_test(
                self._prepare_document_params(rounding_method='round_per_line'),
                [
                    self._prepare_document_cash_rounding('biggest_tax'),
                    self._prepare_document_line_params(32.4, taxes=taxes),
                ],
                {
                    'same_tax_base': True,
                    'currency_id': self.currency_id,
                    'untaxed_amount': 32.40,
                    'tax_amount': 15.700000000000001,
                    'total_amount': 48.1,
                    'subtotals': [
                        {
                            'name': "Untaxed Amount",
                            'base': 32.4,
                            'tax_amount': 15.700000000000001,
                            'tax_groups': [
                                {
                                    'id': self.tax_groups[0].id,
                                    'base': 32.4,
                                    'tax_amount': 2.41,
                                    'display_base': 32.4,
                                    'group_name': self.tax_groups[0].name,
                                },
                                {
                                    'id': self.tax_groups[1].id,
                                    'base': 32.4,
                                    'tax_amount': 1.44,
                                    'display_base': 32.4,
                                    'group_name': self.tax_groups[1].name,
                                },
                                {
                                    'id': self.tax_groups[2].id,
                                    'base': 32.4,
                                    'tax_amount': 0.31,
                                    'display_base': 32.4,
                                    'group_name': self.tax_groups[2].name,
                                },
                                {
                                    'id': self.tax_groups[3].id,
                                    'base': 32.4,
                                    'tax_amount': 4.33,
                                    'display_base': 32.4,
                                    'group_name': self.tax_groups[3].name,
                                },
                                {
                                    'id': self.tax_groups[4].id,
                                    'base': 32.4,
                                    'tax_amount': 7.21,
                                    'cash_rounding_amount': -0.01,
                                    'display_base': 32.4,
                                    'group_name': self.tax_groups[4].name,
                                },
                            ],
                        },
                    ],
                },
            ),
            # Same but exclude some tax groups.
            self._prepare_tax_totals_summary_test(
                self._prepare_document_params(rounding_method='round_per_line'),
                [
                    self._prepare_document_cash_rounding('biggest_tax'),
                    self._prepare_document_line_params(32.4, taxes=taxes),
                ],
                {
                    'same_tax_base': True,
                    'currency_id': self.currency_id,
                    'untaxed_amount': 44.25,
                    'tax_amount': 3.8500000000000005,
                    'total_amount': 48.1,
                    'subtotals': [
                        {
                            'name': "Untaxed Amount",
                            'base': 44.25,
                            'tax_amount': 3.8500000000000005,
                            'tax_groups': [
                                {
                                    'id': self.tax_groups[0].id,
                                    'base': 32.4,
                                    'tax_amount': 2.41,
                                    'display_base': 32.4,
                                    'group_name': self.tax_groups[0].name,
                                },
                                {
                                    'id': self.tax_groups[1].id,
                                    'base': 32.4,
                                    'tax_amount': 1.44,
                                    'display_base': 32.4,
                                    'group_name': self.tax_groups[1].name,
                                },
                            ],
                        },
                    ],
                },
                exclude_tax_group_ids=self.tax_groups[2:5].ids,
            ),
        ]
        self._assert_tests(tests, mode='py')

    def test_exclude_tax_group(self):
        tax1 = self.division_tax(5, tax_group_id=self.tax_groups[0].id)
        tax2 = self.division_tax(3, tax_group_id=self.tax_groups[1].id)
        tax3 = self.division_tax(0.65, tax_group_id=self.tax_groups[2].id)
        tax4 = self.division_tax(9, tax_group_id=self.tax_groups[3].id)
        tax5 = self.division_tax(15, tax_group_id=self.tax_groups[4].id)
        taxes = tax1 + tax2 + tax3 + tax4 + tax5

        tests = [
            self._prepare_tax_totals_summary_test(
                self._prepare_document_params(rounding_method='round_per_line'),
                [
                    self._prepare_document_cash_rounding('biggest_tax'),
                    self._prepare_document_line_params(32.4, taxes=taxes),
                ],
                {
                    'same_tax_base': True,
                    'currency_id': self.currency_id,
                    'untaxed_amount': 44.25,
                    'tax_amount': 3.8500000000000005,
                    'total_amount': 48.1,
                    'subtotals': [
                        {
                            'name': "Untaxed Amount",
                            'base': 44.25,
                            'tax_amount': 3.8500000000000005,
                            'tax_groups': [
                                {
                                    'id': self.tax_groups[0].id,
                                    'base': 32.4,
                                    'tax_amount': 2.41,
                                    'display_base': 32.4,
                                    'group_name': self.tax_groups[0].name,
                                },
                                {
                                    'id': self.tax_groups[1].id,
                                    'base': 32.4,
                                    'tax_amount': 1.44,
                                    'display_base': 32.4,
                                    'group_name': self.tax_groups[1].name,
                                },
                            ],
                        },
                    ],
                },
                exclude_tax_group_ids=self.tax_groups[2:5].ids,
            ),
        ]
        self._assert_tests(tests, mode='py')

    def test_mixed_combined_standalone_taxes(self):
        """ Test when the same taxes are used both as standalone tax and combined all together. """
        tests = []
        tax_10 = self.percent_tax(10.0)
        tax_10_incl_base = self.percent_tax(10.0, include_base_amount=True)
        tax_20 = self.percent_tax(20.0)
        taxes = tax_10 + tax_20 + tax_10_incl_base

        with self.same_tax_group(taxes):
            tests.extend([
                self._prepare_tax_totals_summary_test(
                    self._prepare_document_params(),
                    [
                        self._prepare_document_line_params(1000.0, taxes=tax_10 + tax_20),
                        self._prepare_document_line_params(1000.0, taxes=tax_10),
                        self._prepare_document_line_params(1000.0, taxes=tax_20),
                    ],
                    {
                        'same_tax_base': True,
                        'currency_id': self.currency_id,
                        'untaxed_amount': 3000.0,
                        'tax_amount': 600.0,
                        'total_amount': 3600.0,
                        'subtotals': [
                            {
                                'name': "Untaxed Amount",
                                'base': 3000.0,
                                'tax_amount': 600.0,
                                'tax_groups': [
                                    {
                                        'id': self.tax_groups[0].id,
                                        'base': 3000.0,
                                        'tax_amount': 600.0,
                                        'display_base': 3000.0,
                                        'group_name': self.tax_groups[0].name,
                                    },
                                ],
                            },
                        ],
                    },
                ),
                self._prepare_tax_totals_summary_test(
                    self._prepare_document_params(),
                    [
                        self._prepare_document_line_params(1000.0, taxes=tax_10_incl_base + tax_20),
                        self._prepare_document_line_params(1000.0, taxes=tax_10_incl_base),
                        self._prepare_document_line_params(1000.0, taxes=tax_20),
                    ],
                    {
                        'same_tax_base': True,
                        'currency_id': self.currency_id,
                        'untaxed_amount': 3000.0,
                        'tax_amount': 620.0,
                        'total_amount': 3620.0,
                        'subtotals': [
                            {
                                'name': "Untaxed Amount",
                                'base': 3000.0,
                                'tax_amount': 620.0,
                                'tax_groups': [
                                    {
                                        'id': self.tax_groups[0].id,
                                        'base': 3000.0,
                                        'tax_amount': 620.0,
                                        'display_base': 3000.0,
                                        'group_name': self.tax_groups[0].name,
                                    },
                                ],
                            },
                        ],
                    },
                ),
            ])

        with self.different_tax_group(taxes):
            tests.extend([
                self._prepare_tax_totals_summary_test(
                    self._prepare_document_params(),
                    [
                        self._prepare_document_line_params(1000.0, taxes=tax_10 + tax_20),
                        self._prepare_document_line_params(1000.0, taxes=tax_10),
                        self._prepare_document_line_params(1000.0, taxes=tax_20),
                    ],
                    {
                        'same_tax_base': True,
                        'currency_id': self.currency_id,
                        'untaxed_amount': 3000.0,
                        'tax_amount': 600.0,
                        'total_amount': 3600.0,
                        'subtotals': [
                            {
                                'name': "Untaxed Amount",
                                'base': 3000.0,
                                'tax_amount': 600.0,
                                'tax_groups': [
                                    {
                                        'id': self.tax_groups[0].id,
                                        'base': 2000.0,
                                        'tax_amount': 200.0,
                                        'display_base': 2000.0,
                                        'group_name': self.tax_groups[0].name,
                                    },
                                    {
                                        'id': self.tax_groups[1].id,
                                        'base': 2000.0,
                                        'tax_amount': 400.0,
                                        'display_base': 2000.0,
                                        'group_name': self.tax_groups[1].name,
                                    },
                                ],
                            },
                        ],
                    },
                ),
                self._prepare_tax_totals_summary_test(
                    self._prepare_document_params(),
                    [
                        self._prepare_document_line_params(1000.0, taxes=tax_10_incl_base + tax_20),
                        self._prepare_document_line_params(1000.0, taxes=tax_10_incl_base),
                        self._prepare_document_line_params(1000.0, taxes=tax_20),
                    ],
                    {
                        'same_tax_base': False,
                        'currency_id': self.currency_id,
                        'untaxed_amount': 3000.0,
                        'tax_amount': 620.0,
                        'total_amount': 3620.0,
                        'subtotals': [
                            {
                                'name': "Untaxed Amount",
                                'base': 3000.0,
                                'tax_amount': 620.0,
                                'tax_groups': [
                                    {
                                        'id': self.tax_groups[1].id,
                                        'base': 2100.0,
                                        'tax_amount': 420.0,
                                        'display_base': 2100.0,
                                        'group_name': self.tax_groups[1].name,
                                    },
                                    {
                                        'id': self.tax_groups[2].id,
                                        'base': 2000.0,
                                        'tax_amount': 200.0,
                                        'display_base': 2000.0,
                                        'group_name': self.tax_groups[2].name,
                                    },
                                ],
                            },
                        ],
                    },
                ),
            ])

        self._assert_tests(tests, mode='py')

    def test_preceding_subtotal(self):
        self.tax_groups[1].preceding_subtotal = "PRE GROUP 1"
        self.tax_groups[2].preceding_subtotal = "PRE GROUP 2"
        tax_10 = self.percent_tax(10.0, tax_group_id=self.tax_groups[1].id)
        tax_25 = self.percent_tax(25.0, tax_group_id=self.tax_groups[2].id)
        tax_42 = self.percent_tax(42.0, tax_group_id=self.tax_groups[0].id)

        tests = [
            self._prepare_tax_totals_summary_test(
                self._prepare_document_params(),
                [
                    self._prepare_document_line_params(1000.0),
                    self._prepare_document_line_params(1000.0, taxes=tax_10),
                    self._prepare_document_line_params(1000.0, taxes=tax_25),
                    self._prepare_document_line_params(100.0, taxes=tax_42),
                    self._prepare_document_line_params(200.0, taxes=tax_42 + tax_10 + tax_25),
                ],
                {
                    'same_tax_base': False,
                    'currency_id': self.currency_id,
                    'untaxed_amount': 3300.0,
                    'tax_amount': 546.0,
                    'total_amount': 3846.0,
                    'subtotals': [
                        {
                            'name': "Untaxed Amount",
                            'base': 3300.0,
                            'tax_amount': 126.0,
                            'tax_groups': [
                                {
                                    'id': self.tax_groups[0].id,
                                    'base': 300.0,
                                    'tax_amount': 126.0,
                                    'display_base': 300.0,
                                    'group_name': self.tax_groups[0].name,
                                },
                            ],
                        },
                        {
                            'name': "PRE GROUP 1",
                            'base': 3426.0,
                            'tax_amount': 120.0,
                            'tax_groups': [
                                {
                                    'id': self.tax_groups[1].id,
                                    'base': 1200.0,
                                    'tax_amount': 120.0,
                                    'display_base': 1200.0,
                                    'group_name': self.tax_groups[1].name,
                                },
                            ],
                        },
                        {
                            'name': "PRE GROUP 2",
                            'base': 3546.0,
                            'tax_amount': 300.0,
                            'tax_groups': [
                                {
                                    'id': self.tax_groups[2].id,
                                    'base': 1200.0,
                                    'tax_amount': 300.0,
                                    'display_base': 1200.0,
                                    'group_name': self.tax_groups[2].name,
                                },
                            ],
                        },
                    ],
                },
            ),
        ]

        self.tax_groups[3].preceding_subtotal = "PRE GROUP 1"  # same as tax_groups[1], on purpose
        tax_10.tax_group_id = self.tax_groups[3]  # preceding_subtotal == "PRE GROUP 1"
        tax_42.tax_group_id = self.tax_groups[1]  # preceding_subtotal == "PRE GROUP 1"
        tax_minus_25 = self.percent_tax(-25.0, tax_group_id=self.tax_groups[2].id)  # preceding_subtotal == "PRE GROUP 2"
        tax_30 = self.percent_tax(30.0, tax_group_id=self.tax_groups[0].id)

        tests.append(
            self._prepare_tax_totals_summary_test(
                self._prepare_document_params(),
                [
                    self._prepare_document_line_params(100.0, taxes=tax_10),
                    self._prepare_document_line_params(100.0, taxes=tax_minus_25 + tax_42 + tax_30),
                    self._prepare_document_line_params(200.0, taxes=tax_10 + tax_minus_25),
                    self._prepare_document_line_params(1000.0, taxes=tax_30),
                    self._prepare_document_line_params(100.0, taxes=tax_30 + tax_10),
                ],
                {
                    'same_tax_base': False,
                    'currency_id': self.currency_id,
                    'untaxed_amount': 1500.0,
                    'tax_amount': 367.0,
                    'total_amount': 1867.0,
                    'subtotals': [
                        {
                            'name': "Untaxed Amount",
                            'base': 1500.0,
                            'tax_amount': 360.0,
                            'tax_groups': [
                                {
                                    'id': self.tax_groups[0].id,
                                    'base': 1200.0,
                                    'tax_amount': 360.0,
                                    'display_base': 1200.0,
                                    'group_name': self.tax_groups[0].name,
                                },
                            ],
                        },
                        {
                            'name': "PRE GROUP 1",
                            'base': 1860.0,
                            'tax_amount': 82.0,
                            'tax_groups': [
                                {
                                    'id': self.tax_groups[1].id,
                                    'base': 100.0,
                                    'tax_amount': 42.0,
                                    'display_base': 100.0,
                                    'group_name': self.tax_groups[1].name,
                                },
                                {
                                    'id': self.tax_groups[3].id,
                                    'base': 400.0,
                                    'tax_amount': 40.0,
                                    'display_base': 400.0,
                                    'group_name': self.tax_groups[3].name,
                                },
                            ],
                        },
                        {
                            'name': "PRE GROUP 2",
                            'base': 1942.0,
                            'tax_amount': -75.0,
                            'tax_groups': [
                                {
                                    'id': self.tax_groups[2].id,
                                    'base': 300.0,
                                    'tax_amount': -75.0,
                                    'display_base': 300.0,
                                    'group_name': self.tax_groups[2].name,
                                },
                            ],
                        },
                    ],
                },
            )
        )

        self._assert_tests(tests, mode='py')

    def test_preceding_subtotal_with_tax_group(self):
        self.tax_groups[1].preceding_subtotal = "Tax withholding"
        tax_minus_47 = self.percent_tax(-47.0, tax_group_id=self.tax_groups[1].id)
        tax_10 = self.percent_tax(10.0, tax_group_id=self.tax_groups[0].id)
        tax_group = self.group_of_taxes(tax_minus_47 + tax_10)

        tests = [
            self._prepare_tax_totals_summary_test(
                self._prepare_document_params(),
                [
                    self._prepare_document_line_params(100.0, taxes=tax_group),
                ],
                {
                    'same_tax_base': True,
                    'currency_id': self.currency_id,
                    'untaxed_amount': 100.0,
                    'tax_amount': -37.0,
                    'total_amount': 63.0,
                    'subtotals': [
                        {
                            'name': "Untaxed Amount",
                            'base': 100.0,
                            'tax_amount': 10.0,
                            'tax_groups': [
                                {
                                    'id': self.tax_groups[0].id,
                                    'base': 100.0,
                                    'tax_amount': 10.0,
                                    'display_base': 100.0,
                                    'group_name': self.tax_groups[0].name,
                                },
                            ],
                        },
                        {
                            'name': "Tax withholding",
                            'base': 110.0,
                            'tax_amount': -47.0,
                            'tax_groups': [
                                {
                                    'id': self.tax_groups[1].id,
                                    'base': 100.0,
                                    'tax_amount': -47.0,
                                    'display_base': 100.0,
                                    'group_name': self.tax_groups[1].name,
                                },
                            ],
                        },
                    ],
                },
            ),
        ]

        self._assert_tests(tests, mode='py')

    def test_random_tax_amounts(self):
        tax_16 = self.percent_tax(16.0)
        tax_53 = self.percent_tax(53.0)
        tax_10 = self.percent_tax(10.0)
        tax_23_1 = self.percent_tax(23.0)
        tax_23_2 = self.percent_tax(23.0)
        tax_17a = self.percent_tax(17.0)
        tax_17b = self.percent_tax(17.0)

        tests = [
            self._prepare_tax_amount_test(
                self._prepare_document_params(rounding_method='round_per_line'),
                [self._prepare_document_line_params(100.41, taxes=tax_16 + tax_53)],
                69.29,
            ),
            self._prepare_tax_amount_test(
                self._prepare_document_params(rounding_method='round_globally'),
                [self._prepare_document_line_params(100.41, taxes=tax_16 + tax_53)],
                69.29,
            ),
            self._prepare_tax_amount_test(
                self._prepare_document_params(rounding_method='round_per_line'),
                [
                    self._prepare_document_line_params(50.4, taxes=tax_17a),
                    self._prepare_document_line_params(47.21, taxes=tax_17b),
                ],
                16.60,
            ),
            self._prepare_tax_amount_test(
                self._prepare_document_params(rounding_method='round_globally'),
                [
                    self._prepare_document_line_params(50.4, taxes=tax_17a),
                    self._prepare_document_line_params(47.21, taxes=tax_17b)
                ],
                16.60,
            ),
            self._prepare_tax_amount_test(
                self._prepare_document_params(rounding_method='round_per_line'),
                [
                    self._prepare_document_line_params(50.4, taxes=tax_17a),
                    self._prepare_document_line_params(47.21, taxes=tax_17a),
                ],
                16.60,
            ),
            self._prepare_tax_amount_test(
                self._prepare_document_params(rounding_method='round_globally'),
                [
                    self._prepare_document_line_params(50.4, taxes=tax_17a),
                    self._prepare_document_line_params(47.21, taxes=tax_17a),
                ],
                16.59,
            ),
            self._prepare_tax_amount_test(
                self._prepare_document_params(rounding_method='round_per_line'),
                [
                    self._prepare_document_line_params(54.45, taxes=tax_10),
                    self._prepare_document_line_params(100.0, taxes=tax_10),
                ],
                15.45,
            ),
            self._prepare_tax_amount_test(
                self._prepare_document_params(rounding_method='round_globally'),
                [
                    self._prepare_document_line_params(54.45, taxes=tax_10),
                    self._prepare_document_line_params(100.0, taxes=tax_10),
                ],
                15.45,
            ),
            self._prepare_tax_amount_test(
                self._prepare_document_params(rounding_method='round_per_line'),
                [
                    self._prepare_document_line_params(54.45, taxes=tax_10),
                    self._prepare_document_line_params(600.0, taxes=tax_10),
                    self._prepare_document_line_params(-500.0, taxes=tax_10),
                ],
                15.45,
            ),
            self._prepare_tax_amount_test(
                self._prepare_document_params(rounding_method='round_globally'),
                [
                    self._prepare_document_line_params(54.45, taxes=tax_10),
                    self._prepare_document_line_params(600.0, taxes=tax_10),
                    self._prepare_document_line_params(-500.0, taxes=tax_10),
                ],
                15.44,
            ),
            self._prepare_tax_amount_test(
                self._prepare_document_params(rounding_method='round_per_line'),
                [
                    self._prepare_document_line_params(94.7, taxes=tax_23_1),
                    self._prepare_document_line_params(32.8, taxes=tax_23_2),
                ],
                29.32,
            ),
            self._prepare_tax_amount_test(
                self._prepare_document_params(rounding_method='round_globally'),
                [
                    self._prepare_document_line_params(94.7, taxes=tax_23_1),
                    self._prepare_document_line_params(32.8, taxes=tax_23_2),
                ],
                29.32,
            ),
        ]

        self._assert_tests(tests, mode='py')


class TestRecordsTaxTotalsSummary(TestTaxesTaxTotalsSummary):

    def _get_test_py_tax_totals_summary_results(self, document_values, exclude_tax_group_ids=None):
        # TO BE OVERRIDDEN
        return

    def _prepare_tax_totals_summary_test(
        self,
        create_document_params,
        other_params,
        expected_values,
        exclude_tax_group_ids=None,
    ):
        test = super()._prepare_tax_totals_summary_test(
            create_document_params,
            other_params,
            expected_values,
            exclude_tax_group_ids=exclude_tax_group_ids,
        )
        params = test['params']
        document_values = self._create_document(params['create_document_params'], params['other_params'])
        self.env.company.tax_calculation_rounding_method = document_values['rounding_method']
        test['py_results'] = self._get_test_py_tax_totals_summary_results(document_values, params['exclude_tax_group_ids'])
        return test

    def _assert_tests(self, tests, mode='py_js'):
        super()._assert_tests([test for test in tests if test.get('py_results')], mode='py')

    def _add_test_py_results(self, test):
        return

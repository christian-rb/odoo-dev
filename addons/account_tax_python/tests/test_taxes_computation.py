from odoo.addons.account.tests.test_tax import TestTaxCommon
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestTaxesComputation(TestTaxCommon):

    def python_tax(self, formula, **kwargs):
        self.number += 1
        return self.env['account.tax'].create({
            **kwargs,
            'name': f"code_({self.number})",
            'amount_type': 'code',
            'amount': 0.0,
            'formula': formula,
        })

    def _prepare_test(self, formula, *args, **kwargs):
        tax = self.python_tax(formula, **kwargs.pop('tax_data', {}))
        product_values = kwargs.pop('product_values', None)
        if product_values:
            product = self.env['product.product'].create({
                'name': "_prepare_test",
                **product_values,
            })
            kwargs.setdefault('evaluation_context_kwargs', {})['product'] = product

        return self._prepare_taxes_computation_test(tax, *args, **kwargs)

    def test_formula(self):
        tests = [
            self._prepare_test(
                "max(quantity * price_unit * 0.21, quantity * 4.17)",
                130.0,
                {
                    'total_included': 157.3,
                    'total_excluded': 130.0,
                    'taxes_data': (
                        (130.0, 27.3),
                    ),
                },
            ),
            self._prepare_test(
                "max(quantity * price_unit * 0.21, quantity * 4.17)",
                130.0,
                {
                    'total_included': 130.0,
                    'total_excluded': 102.7,
                    'taxes_data': (
                        (102.7, 27.3),
                    ),
                },
                tax_data={'price_include': True},
            ),
            self._prepare_test(
                "product.volume * quantity * 0.35",
                100.0,
                {
                    'total_included': 135.0,
                    'total_excluded': 100.0,
                    'taxes_data': (
                        (100.0, 35.0),
                    ),
                },
                product_values={'volume': 100.0},
            ),
            self._prepare_test(
                "product.volume > 100 and 10 or 5",
                100.0,
                {
                    'total_included': 110.0,
                    'total_excluded': 100.0,
                    'taxes_data': (
                        (100.0, 10.0),
                    ),
                },
                product_values={'volume': 105.0},
            ),
            self._prepare_test(
                "product.volume > 100 and 10 or 5",
                100.0,
                {
                    'total_included': 105.0,
                    'total_excluded': 100.0,
                    'taxes_data': (
                        (100.0, 5.0),
                    ),
                },
                product_values={'volume': 50.0},
            ),
            self._prepare_test(
                "product.volume > 100 and 5 or None",
                100.0,
                {
                    'total_included': 100.0,
                    'total_excluded': 100.0,
                    'taxes_data': [],
                },
                product_values={'volume': 50.0},
            ),
        ]
        self._assert_tests(tests)

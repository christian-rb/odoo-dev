# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import re

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


REGEX_FORMULA_OBJECT = re.compile(r'((?:product\[\')(?P<field>\w+)(?:\'\]))+')


class AccountTaxPython(models.Model):
    _inherit = "account.tax"

    amount_type = fields.Selection(
        selection_add=[('code', "Custom Formula")],
        ondelete={'code': lambda recs: recs.write({'amount_type': 'percent', 'active': False})},
    )
    formula = fields.Text(
        string="Formula",
        default="price_unit * 0.10",
        help="Compute the amount of the tax.\n\n"
             ":param base: float, actual amount on which the tax is applied\n"
             ":param price_unit: float\n"
             ":param quantity: float\n"
             ":param product: A object representing the product\n"
    )

    @api.constrains('amount_type', 'formula')
    def _check_amount_type_code_formula(self):
        for tax in self:
            if tax.amount_type != 'code':
                continue

            tax_data = tax._prepare_dict_for_taxes_computation()
            product_fields = self._eval_taxes_computation_prepare_product_fields([tax_data])
            default_product_values = self._eval_taxes_computation_prepare_product_default_values(product_fields)
            product_values = self._eval_taxes_computation_prepare_product_values(default_product_values)
            evaluation_context = self._eval_taxes_computation_prepare_context(0.0, 0.0, product_values)
            evaluation_context['extra_base'] = 0.0

            # Even we are evaluated the formula with an empty code, the compiler will check for malformed expression.
            self._eval_tax_amount(tax_data, evaluation_context)

    def _prepare_dict_for_taxes_computation(self):
        # EXTENDS 'account'
        values = super()._prepare_dict_for_taxes_computation()

        if self.amount_type == 'code':
            for key, value in self._decode_formula(self.formula).items():
                values[f'_{key}'] = value

        return values

    @api.model
    def _ascending_process_fixed_taxes_batch(self, batch):
        # EXTENDS 'account'
        super()._ascending_process_fixed_taxes_batch(batch)

        if batch['amount_type'] == 'code':
            batch['is_tax_computed'] = True

    @api.model
    def _descending_process_price_included_taxes_batch(self, batch):
        # EXTENDS 'account'
        super()._descending_process_price_included_taxes_batch(batch)

        if batch['price_include'] and batch['amount_type'] == 'code':
            batch['is_base_computed'] = True

    @api.model
    def _ascending_process_taxes_batch(self, batch):
        # EXTENDS 'account'
        super()._ascending_process_taxes_batch(batch)

        if not batch['price_include'] and batch['amount_type'] == 'code':
            batch['is_base_computed'] = True

    @api.model
    def _eval_taxes_computation_prepare_product_fields(self, taxes_data):
        # EXTENDS 'account'
        field_names = super()._eval_taxes_computation_prepare_product_fields(taxes_data)
        for tax_data in taxes_data:
            if tax_data['amount_type'] == 'code':
                field_names.update(tax_data['_product_fields'])
        return field_names

    def _decode_formula(self, formula):
        """ Decode the formula and extract relevant values from it.

        :param formula: The value of the 'formula' field.
        """
        self.ensure_one()

        if self.amount_type != 'code':
            return {}

        formula = (formula or '0.0').strip()
        results = {
            'js_formula': formula
                .replace('and', '?')
                .replace('or', ':')
                .replace('None', 'undefined'),
            'py_formula': formula,
        }
        product_fields = set()

        groups = re.findall(r'((?:product\.)(?P<field>\w+))+', formula) or []
        Product = self.env['product.product']
        for group in groups:
            field_name = group[1]
            if field_name in Product:
                product_fields.add(field_name)
                results['py_formula'] = results['py_formula'].replace(f"product.{field_name}", f"product['{field_name}']")

        results['product_fields'] = list(product_fields)
        return results

    @api.model
    def _check_formula(self, tax_data):
        """ Check the formula is passing the minimum check to ensure the compatibility between both evaluation
        in python & javascript.

        :param tax_data: The values returned by '_prepare_dict_for_taxes_computation'.
        """
        def startswith_number(formula, i):
            starting_i = i
            seen_separator = False
            while i < len(formula):
                if formula[i].isnumeric():
                    i += 1
                elif formula[i] == '.' and (i - starting_i) > 0 and not seen_separator:
                    i += 1
                    seen_separator = True
                else:
                    break
            return i - starting_i

        formula = tax_data['_py_formula']
        allowed_tokens = {
            '(', ')',
            '+', '-', '*', '/', ',', '<', '>', '<=', '>=',
            'and', 'or', 'None',
            'base', 'quantity', 'price_unit',
            'min', 'max',
        }
        for field_name in tax_data['_product_fields']:
            allowed_tokens.add(f"product['{field_name}']")

        # The condition are managed js-side by replacing 'and' by '?' and 'or' by ':'.
        # However, it only works when 'and' appears before 'or'. It means 'a or b and c' is invalid.
        and_or_counter = 0

        def raise_malformed():
            raise ValidationError(_("Malformed formula '%s' at %s", formula, i))

        i = 0
        while i < len(formula):

            if formula[i] == ' ':
                i += 1
                continue

            continue_needed = False
            for token in allowed_tokens:
                if formula[i:i + len(token)] == token:

                    # and/or.
                    if token == 'and':
                        and_or_counter += 1
                    elif token == 'or':
                        if and_or_counter == 0:
                            raise_malformed()
                        and_or_counter -= 1

                    i += len(token)
                    continue_needed = True
                    break
            if continue_needed:
                continue

            number_size = startswith_number(formula, i)
            if number_size > 0:
                i += number_size
                continue

            raise_malformed()

        if and_or_counter:
            raise_malformed()

    @api.model
    def _eval_tax_amount_formula(self, tax_data, evaluation_context):
        """ Evaluate the formula of the tax passed as parameter.

        [!] Mirror of the same method in account_tax.js.
        PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.

        :param tax_data:          The values of a tax returned by '_prepare_taxes_computation'.
        :param evaluation_context:  The context created by '_eval_taxes_computation_prepare_context'.
        :return:                    The tax base amount.
        """
        self._check_formula(tax_data)

        # Save eval.
        raw_base = (evaluation_context['quantity'] * evaluation_context['price_unit']) + evaluation_context['extra_base']
        formula_context = {
            'price_unit': evaluation_context['price_unit'],
            'quantity': evaluation_context['quantity'],
            'product': evaluation_context['product'],
            'base': raw_base,
            'min': min,
            'max': max,
        }
        try:
            return safe_eval(
                tax_data['_py_formula'],
                globals_dict=formula_context,
                locals_dict={},
                globals_builtins=False,
                locals_builtins=False,
                nocopy=True,
            )
        except ZeroDivisionError:
            return 0.0

    @api.model
    def _eval_tax_amount(self, tax_data, evaluation_context):
        # EXTENDS 'account'
        if tax_data['amount_type'] == 'code':
            return self._eval_tax_amount_formula(tax_data, evaluation_context)
        return super()._eval_tax_amount(tax_data, evaluation_context)

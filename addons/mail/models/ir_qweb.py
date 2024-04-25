# -*- coding: utf-8 -*-

import ast
import functools

from odoo import models


class IrQweb(models.AbstractModel):
    """Add ``raise_on_code`` option for qweb. When this option is activated
    then all directives are prohibited.
    """

    _inherit = "ir.qweb"

    # QWeb expressions allowed if we are not template editor
    allowed_qweb_expressions = {
        "object.name",
        "object.contact_name",
        "object.partner_id.name",
    }

    ast_allowed_qweb_expressions = {ast.parse(e) for e in allowed_qweb_expressions}

    def _get_template_cache_keys(self):
        return super()._get_template_cache_keys() + ["raise_on_code"]


    def _compile_directive(self, el, compile_context, directive, level):
        if compile_context.get("raise_on_code") and directive not in ("esc", "out", "inner-content", "att", "tag-open", "tag-close"):
            raise PermissionError("This rendering mode prohibits the use of directives.")
        return super()._compile_directive(el, compile_context, directive, level)


    def _compile_expr(self, expr, raise_on_missing=False):
        if self.env.context.get("raise_on_code") and not self._is_expression_allowed(expr):
            raise PermissionError("This rendering mode prohibits the use of directives.")
        return super()._compile_expr(expr, raise_on_missing)

    @functools.lru_cache(maxsize=2048)
    def _is_expression_allowed(self, expr):
        if expr in self.allowed_qweb_expressions:
            return True

        ast_expr = ast.parse(expr)
        if len(ast_expr.body) != 1:
            return False

        try:
            ast_default_node = ast_expr.body[0].value.values[1].value
        except AttributeError:
            return False

        if not isinstance(ast_default_node, str):
            return False

        for ast_allowed_qweb_expression in self.ast_allowed_qweb_expressions:
            # allow default value
            # >>> object.name or 'Alice'
            expected = ast.Module(
                body=[
                    ast.Expr(
                        value=ast.BoolOp(
                            op=ast.Or(),
                            values=[
                                ast.parse(ast_allowed_qweb_expression).body[0].value,
                                ast.Constant(value=ast_default_node),
                            ],
                        )
                    )
                ],
                type_ignores=[],
            )
            if ast.unparse(expected) == ast.unparse(ast_expr):
                return True
        return False

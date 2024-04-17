# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api

# TODO edm: see other solution first, don't delete that one yet.
class pdf_quote_builder_form_model_fields(models.Model):
    """ Fields configuration for the sale pdf quote builder"""
    _name = 'ir.model.fields'
    _description = 'Fields'
    _inherit = 'ir.model.fields'

    def init(self):
        # set all existing unset pdf_quote_builder_form_blacklisted fields to ``true``, to use it as
        # a whitelist rather than a blacklist
        self._cr.execute(
            'UPDATE ir_model_fields'
            ' SET pdf_quote_builder_form_blacklisted=true'
            ' WHERE pdf_quote_builder_form_blacklisted IS NULL'
        )
        # add an SQL-level default value on pdf_quote_builder_form_blacklisted to that
        # pure-SQL ir.model.field creations (e.g. in _reflect) generate
        # the right default value for a whitelist (aka fields should be
        # blacklisted by default)  TODO edm: investigate that
        self._cr.execute('ALTER TABLE ir_model_fields '
                         ' ALTER COLUMN pdf_quote_builder_form_blacklisted SET DEFAULT true')

    @api.model
    def pdf_quote_builder_form_field_whitelist(self, model, fields):
        """
        :param str model: name of the model on which to whitelist fields
        :param list(str) fields: list of fields to whitelist on the model
        :return: nothing of import
        """
        # postgres does *not* like ``in [EMPTY TUPLE]`` queries
        if not fields:
            return False

        if not self.env['res.users'].has_group('base.group_system'):
            return False

        unexisting_fields = [field for field in fields if field not in self.env[model]._fields.keys()]
        if unexisting_fields:
            raise ValueError("Unable to whitelist field(s) %r for model %r." % (unexisting_fields, model))

        # the ORM only allows writing on custom fields and will trigger a
        # registry reload once that's happened. We want to be able to
        # whitelist non-custom fields and the registry reload absolutely
        # isn't desirable, so go with a method and raw SQL
        # TODO edm: wut? Understand that
        self.env.cr.execute(
            "UPDATE ir_model_fields"
            " SET pdf_quote_builder_form_blacklisted=false"
            " WHERE model=%s AND name in %s", (model, tuple(fields)))
        return True

    pdf_quote_builder_form_blacklisted = fields.Boolean(
        string='Blacklisted in pdf quote builder forms',
        help='Blacklist this field for pdf quote builder forms',
        default=True,
    )
    # TODO edm: index=True ?

# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PDFQuoteBuilderFormFieldWhitelist(models.Model):
    """TODO edm
    """
    _name = 'pdf.quote.builder.form.field.whitelist'
    _description = "Sale PDF Quote Builder Form Fields Whitelist"
    _log_access = False  # TODO edm: not required, but these logs are useless for this model

    # TODO edm: order params
    res_name = fields.Char(string="Resource Name", compute='_compute_res_name')
    res_model = fields.Char(string="Resource Model", required=True)
    res_field = fields.Char(string="Resource Field", required=True)
    # TODO edm: ensure existing
    product_document_ids = fields.Many2many(
        comodel_name='product.document',
        string="Product Document",
        help="Product Document PDF using this protected field."
    )
    # TODO edm: header and footer are direct binary fields. Add traces here too
    company_id = fields.Many2one(
        'res.company', string="Company", default=lambda self: self.env.company
    )

    @api.constrains('res_model', 'res_field')
    def _constrains_valid_model_and_fields_names(self):
        for entry in self:
            names = {entry.res_model, entry.res_field}
            entry._ensure_names_follows_pattern(names)
            Model = entry._get_existing_model()  # Raise if not existing
            entry._get_existing_field_info(Model)  # Raise if not existing

    @api.depends('res_model', 'res_field')
    def _compute_res_name(self):
        for entry in self:
            names = {entry.res_model, entry.res_field}
            self._ensure_names_follows_pattern(names)
            if entry.res_model and entry.res_field:
                Model = entry._get_existing_model()
                field_info = entry._get_existing_field_info(Model)
                entry.res_name = _(
                    "Field %(field_name)s from model %(model_name)s",
                    field_name=field_info['string'],
                    model_name=Model._description
                )
            else:
                entry.res_name = False

    def _ensure_names_follows_pattern(self, names):
        """TODO edm (alphanum or -) once or more (. (alphanum or -) once or more) zero or more
        """
        name_pattern = re.compile(r'^(\w|-)+(\.(\w|-)+)*$')
        if any(not re.match(name_pattern, name) for name in names if name):  # name could be False
            raise ValidationError(_(
                "Invalid resource names. It should only contain alphanumerics, points, hyphen"
                " or underscores."
            ))

    def _get_existing_model(self):
        self.ensure_one()
        Model = self.env.get(self.res_model, 'error')
        if Model:  # Model should be falsy, as it should be an empty recordset
            raise ValidationError(_("This model doesn't exist"))
        return Model

    def _get_existing_field_info(self, Model):
        field_info = Model.fields_get().get(self.res_field)
        if not field_info:
            raise ValidationError(_(
                "The field %(field_name)s doesn't exist on model %(model_name)s",
                field_name=self.res_field,
                model_name=Model._name
            ))
        return field_info

    def unlink(self):
        if not self:
            return True
        # TODO edm
        res = None
        return res


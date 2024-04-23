# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.sale_pdf_quote_builder import utils


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
            utils._ensure_names_follows_pattern(names)
            Model = entry._get_existing_model()  # Raise if not existing
            utils._get_existing_field_info(entry.res_model, Model)  # Raise if not existing

    @api.depends('res_model', 'res_field')
    def _compute_res_name(self):
        for entry in self:
            names = {entry.res_model, entry.res_field}
            utils._ensure_names_follows_pattern(names)
            if entry.res_model and entry.res_field:
                Model = entry._get_existing_model()
                field_info = utils._get_existing_field_info(entry.res_model, Model)
                entry.res_name = _(
                    "Field %(field_name)s from model %(model_name)s",
                    field_name=field_info['string'],
                    model_name=Model._description
                )
            else:
                entry.res_name = False

    def _get_existing_model(self):
        self.ensure_one()
        Model = self.env.get(self.res_model, 'error')
        if Model:  # Model should be falsy, as it should be an empty recordset
            raise ValidationError(_("This model doesn't exist"))
        return Model

    def unlink(self):
        if not self:
            return True
        # TODO edm
        res = None
        return res


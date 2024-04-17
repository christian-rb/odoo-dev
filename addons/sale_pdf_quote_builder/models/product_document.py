# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import io

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import pdf


class ProductDocument(models.Model):
    _inherit = 'product.document'

    attached_on = fields.Selection(
        selection_add=[('inside', "Inside quote pdf")],
        help="Allows you to share the document with your customers within a sale.\n"
             "Leave it empty if you don't want to share this document with sales customer.\n"
             "On quote: the document will be sent to and accessible by customers at any time.\n"
             "e.g. this option can be useful to share Product description files.\n"
             "On order confirmation: the document will be sent to and accessible by customers.\n"
             "e.g. this option can be useful to share User Manual or digital content bought on"
             " ecommerce. \n"
             "Inside quote pdf: The document will be included in the pdf of the quotation between"
             " the header pages and the quote table. ",
        ondelete={'inside': 'set default'},
    )
    has_restricted_form_fields = fields.Boolean(compute='_compute_has_restricted_form_fields')

    # === COMPUTE METHODS ===#

    @api.depends('datas')
    def _compute_has_restricted_form_fields(self):
        for doc in self:
            # When loading a file, the mimetype isn't set yet, as it's set when saving.
            mimetype = doc.mimetype or (doc.datas and self.env['ir.attachment']._compute_mimetype(
                {'datas': doc.datas}
            ))

            if mimetype != 'application/pdf':
                doc.has_restricted_form_fields = False
                continue

            restricted_fields = doc._get_restricted_form_fields()
            doc.has_restricted_form_fields = bool(restricted_fields)

    # === ONCHANGE METHODS ===#

    @api.onchange('attached_on', 'has_restricted_form_fields')
    def _onchange_avoid_restricted_fields_attached_inside(self):
        # In order to avoid the save from triggering the constraint before adding the fields to the
        # whitelist, we force the attached_on to hidden when some fields are not yet whitelisted.
        for doc in self:
            if doc.attached_on == 'inside' and doc.has_restricted_form_fields:
                doc.attached_on = 'hidden'
                message = _(
                    "This file contains restricted form fields. Until these fields as mark as being"
                    " allowed, you cannot set this file as being attached inside the quote. It was"
                    " changed as hidden.\n"
                )
                if not self.env.user.has_group('base.group_system'):
                    message += _("Please contact an administrator to authorized these fields.")
                else:
                    message += _(
                        "Please mark down these fields as safe by clicking on the \"Allow new"
                        " fields\" button, and follow the instructions."
                    )
                return {
                    'warning': {
                        'title': _("Warning"),
                        'message': message
                    }
                }

    # === CONSTRAINT METHODS ===#

    @api.constrains('attached_on', 'datas')
    def _check_attached_on_and_datas_compatibility(self):
        for doc in self:
            if doc.attached_on == 'inside' and not (doc.datas and doc.mimetype.endswith('pdf')):
                raise ValidationError(_("Only PDF documents can be attached inside a quote."))

    @api.constrains('attached_on', 'datas')
    def _ensure_no_restricted_fields(self):
        inside_docs = self.filtered(lambda d: d.attached_on == 'inside')
        has_admin_rights = self.env.user.has_group('base.group_system')
        has_restricted_inside_docs = any([doc._get_restricted_form_fields() for doc in inside_docs])
        if has_restricted_inside_docs and not has_admin_rights:
            raise ValidationError(_(
                "Only PDF documents without restricted form fields can be attached inside a"
                " quote. In order to mark a field as allowed, please ask you administrator to"
                " add this pdf and follow the directions."
            ))
        if has_restricted_inside_docs and has_admin_rights:
            # TODO edm: error message
            raise ValidationError(_(
                "Only PDF documents without restricted form fields can be attached inside a"
                " quote. In order to mark a field as allowed, please blablabla"
            ))

    # === ACTION METHODS ===#

    def action_open_whitelisting_wizard(self):
        self.ensure_one()
        restricted_fields = self._get_restricted_form_fields()
        return {
            'name': _("Whitelisting PDF Form Fields"),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sale.pdf.quote.builder.whitelisting.wizard',
            'target': 'new',
            'context': {
                'active_model': 'product.document',
                'active_ids': self.id,
            },
        }

    # === BUSINESS METHODS ===#

    def _get_restricted_form_fields(self):
        # TODO edm docstring, ensure mimetypde can't be done here because of the onchange where the mimetype has to be manually computed.
        restricted_fields = set()
        for doc in self:
            # Without bin_size=False, size is returned instead of content when saving the file.
            # But in compute and onchange, setting that context will empty the datas.
            doc = doc if doc.datas.startswith(b'JVBERi0') else doc.with_context(bin_size=False)
            reader = pdf.PdfFileReader(io.BytesIO(base64.b64decode(doc.datas)))
            pdf_fields = reader.getFields() or {}
            whitelisted_fields = {}  # TODO edm
            restricted_fields |= {f for f in pdf_fields if f not in whitelisted_fields}
            # TODO edm: sanitize fields
        return restricted_fields

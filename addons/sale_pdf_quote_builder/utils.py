# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import io
import re

from odoo import _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import pdf


def _ensure_names_follows_pattern(names):
    """TODO edm (alphanum or -) once or more (. (alphanum or -) once or more) zero or more
    """
    name_pattern = re.compile(r'^(\w|-)+(\.(\w|-)+)*$')
    name_pattern = re.compile(r'^(\w|-)+$')
    if any(not re.match(name_pattern, name) for name in names if name):  # name could be False TODO edm: might not be the case anymore
        raise ValidationError(_(
            "Invalid resource names. It should only contain alphanumerics, points, hyphen"
            " or underscores."
        ))

def _get_existing_field_info(res_field, Model):
    field_info = Model.fields_get().get(res_field)
    if not field_info:
        raise ValidationError(_(
            "The field %(field_name)s doesn't exist on model %(model_name)s",
            field_name=res_field,
            model_name=Model._name
        ))
    return field_info

def _get_restricted_form_fields(BaseModel, docs):
    # TODO edm docstring, ensure mimetypde can't be done here because of the onchange where the mimetype has to be manually computed.
    restricted_fields = set()
    # whitelisted_fields = docs.env['pdf.quote.builder.form.field.whitelist'].search([])  # TODO edm
    for doc in docs:
        # Without bin_size=False, size is returned instead of content when saving the file.
        # But in compute and onchange, setting that context will empty the datas.
        doc = doc if doc.datas.startswith(b'JVBERi0') else doc.with_context(bin_size=False)
        reader = pdf.PdfFileReader(io.BytesIO(base64.b64decode(doc.datas)))
        raw_pdf_fields = reader.getFields() or set()
        _ensure_names_follows_pattern(raw_pdf_fields)
        pdf_models_and_fields = _get_model_and_fields(BaseModel, raw_pdf_fields)
        print(pdf_models_and_fields)
        temporary_whitelist = {('res.company', 'name'), ('sale.order.line', 'display_type'), ('product.product', 'name'), ('sale.order', 'name'), ('sale.order.line', 'state'), ('sale.order.line', 'name')}  # TODO edm
        restricted_fields |= {mf for mf in pdf_models_and_fields if mf not in temporary_whitelist}
        print("restricted_field: ", restricted_fields)
        # TODO edm: sanitize fields
    return restricted_fields


def _get_model_and_fields(BaseModel, field_names):
    model_and_fields = set()
    for name in field_names:  # TODO edm: deque?
        chain = name.split('__')
        # chain = collections.deque(chain)
        Model = BaseModel
        field = ''
        for elem in chain:
            if elem == chain[-1]:
                field = elem
            else:
                Model = Model[elem]
        model_and_fields.add((Model._name, field))
    return model_and_fields

def _get_field_format(field, order):
    # TODO edm: sol names are prefixed by the sol id
    # TODO edm: but if 100+ elem ==> this is done a hundred times... =/
    chain = field.split('__')
    is_sol = chain[0].startswith('sol_id_')
    BaseModel = order.env['sale.order'] if not is_sol else order.env['sale.order.line']
    chain = chain if not is_sol else chain[1:]
    Model = BaseModel
    res_field = ''
    field_type = None
    for elem in chain:
        if elem == chain[-1]:
            res_field = elem
            field_type = _get_existing_field_info(res_field, Model)['type']
            print(field_type)
        else:
            Model = Model[elem]
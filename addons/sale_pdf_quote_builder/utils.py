# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import io
import re

from odoo import _
from odoo.exceptions import ValidationError
from odoo.tools import format_amount, format_date, format_datetime, pdf

def _ensure_names_follows_pattern(names):
    """TODO edm (alphanum (this include underscore) or -) once or more ( at this point, we didn't replace __ by . yet, so no need to cover that case)
    """
    name_pattern = re.compile(r'^(\w|-)+$')
    if names and any(not re.match(name_pattern, name) for name in names):  # name could be False TODO edm: might not be the case anymore
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
        path = name.split('__')
        # chain = collections.deque(chain)
        Model = BaseModel
        field = ''
        for elem in path:
            if elem == path[-1]:
                field = elem
            else:
                Model = Model[elem]
        model_and_fields.add((Model._name, field))
    return model_and_fields

def _get_field_format(field, order, env, tz, lang_code):
    # TODO edm: sol names are prefixed by the sol id
    # TODO edm: but if 100+ elem ==> this is done a hundred times... =/
    path = field.split('__')
    is_sol = path[0].startswith('sol_id_')

    if not is_sol:  # Header or footer
        BaseModel = order.env['sale.order']
        value = order
    else:  # Product document
        BaseModel = order.env['sale.order.line']
        line_id = int(path[0].strip('sol_id_'))
        value = order.order_line.browse(line_id)
        path = path[1:]

    Model = BaseModel

    for elem in path[:-1]:
        Model, value = Model[elem], value[elem]
        # TODO edm: isn't it possible to get the model from the value while it's not the end value?
        # TODO edm: would it be possible to pass the path minus last and get the needed information?

    value = value[path[-1]]
    field_info = _get_existing_field_info(path[-1], Model)
    field_type = field_info['type']
    print("field_type: ", field_type)
    print("value: ", value)

    # TODO edm: factorize
    if field_type == 'boolean':
        formatted_value = value
    elif field_type == 'integer':
        formatted_value = value
    elif field_type == 'float':
        formatted_value = value
    elif field_type == 'monetary':
        # TODO edm: wrong, should take the currency_field of the record, not the order
        formatted_value = format_amount(env, value, order.currency_id)
    elif field_type == 'char':  # translated?
        formatted_value = value
    elif field_type == 'text':
        formatted_value = value  # translated?
    elif field_type == 'html':
        formatted_value = ''  # TODO edm: decide, passing or not?
    elif field_type == 'date':
        formatted_value = format_date(env, value, lang_code=lang_code)
    elif field_type == 'datetime':
        formatted_value = format_datetime(env, value, tz=tz)
    elif field_type == 'binary':  # TODO edm: I don't see a case where we want to send that.
        formatted_value = ''  # TODO edm: decide, passing or not?
    elif field_type == 'selection' and value:  # is it already translated?
        selection_dict = {k:v for k, v in field_info['selection']}
        formatted_value = selection_dict[value]
    elif field_type == 'reference':  # TODO edm: I don't see a case where we want to send that.
        formatted_value = ''  # TODO edm: decide, passing or not?
    elif field_type == 'many2one':
        formatted_value = ''  # TODO edm: decide, passing or not?
    elif field_type == 'many2one_reference':  # TODO edm: I don't see a case where we want to send that.
        formatted_value = ''  # TODO edm: decide, passing or not?
    elif field_type == 'json':
        formatted_value = ''  # TODO edm: decide, passing or not?
    elif field_type == 'properties':  # TODO edm: I don't see a case where we want to send that.
        formatted_value = ''  # TODO edm: decide, passing or not?
    elif field_type == 'properties_definition':  # TODO edm: I don't see a case where we want to send that.
        formatted_value = ''  # TODO edm: decide, passing or not?
    elif field_type == 'one2many':
        formatted_value = ''  # TODO edm: decide, passing or not?
    elif field_type == 'many2many':
        formatted_value = ''  # TODO edm: decide, passing or not?

    else:
        formatted_value = value
        # TODO edm: everything else

    return formatted_value or ''
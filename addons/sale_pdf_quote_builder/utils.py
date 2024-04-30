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
            "Invalid resource names. It should only contain alphanumerics, hyphens or underscores."
        ))

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
        temporary_whitelist = {('sale.order', 'date_order'), ('sale.order', 'tax_totals'), ('sale.order.line', 'display_type'), ('sale.order.line', 'price_total'), ('product.product', 'active'), ('sale.order.line', 'name'), ('sale.order', 'note'), ('sale.order.line', 'product_uom_qty'), ('product.product', 'product_template_attribute_value_ids'), ('sale.order', 'commitment_date'), ('sale.order', 'order_line'), ('product.product', 'default_code'), ('sale.order', 'validity_date'), ('sale.order.line', 'order_id'), ('product.product', 'product_document_count'), ('product.product', 'image_128'), ('sale.order.line', 'state')}  # TODO edm
        restricted_fields |= {mf for mf in pdf_models_and_fields if mf not in temporary_whitelist}
    return restricted_fields


def _get_model_and_fields(BaseModel, field_names):
    model_and_fields = set()
    for name in field_names:  # TODO edm: deque?
        path = name.split('__')
        # chain = collections.deque(chain)  # TODO edm. Or is it possible to have something built in for this?
        Model = BaseModel
        field = ''
        for elem in path:
            if elem == path[-1]:
                field = elem
            else:
                field_info = Model.fields_get().get(elem)
                if not field_info:
                    raise ValidationError(_(
                        "The field %(field_name)s doesn't exist on model %(model_name)s",
                        field_name=elem,
                        model_name=Model._name
                    ))
                Model = Model[elem]
        model_and_fields.add((Model._name, field))
    return model_and_fields

def _get_field_format(field, order, env, tz, lang_code):
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

    for elem in path[:-1]:  # TODO edm: but if 100+ chained elem ==> this is done a hundred times... =/
        Model, value = Model[elem], value[elem]
        # TODO edm: isn't it possible to get the model from the value while it's not the end value?
        # TODO edm: would it be possible to pass the path minus last and get the needed information?

    value = value[path[-1]]
    field_info = Model.fields_get().get(path[-1])
    field_type = field_info['type']

    if field_type == 'boolean':  # Todo edm: let this value?
        formatted_value = _("Yes") if value else _("No")
    elif field_type == 'monetary':
        # TODO edm: wrong, should take the currency_field of the record, not the order
        formatted_value = format_amount(env, value, order.currency_id)
    elif field_type == 'date':
        formatted_value = format_date(env, value, lang_code=lang_code)
    elif field_type == 'datetime':
        formatted_value = format_datetime(env, value, tz=tz)
    elif field_type == 'selection' and value:
        selection_dict = {k:v for k, v in field_info['selection']}
        formatted_value = selection_dict[value]
    elif field_type in {'one2many', 'many2one', 'many2many'}:
        for elem in {'name', 'title', 'description'}:
            name_key = elem if value.fields_get().get(elem) else None
            if name_key:
                break
        formatted_value = ', '.join([v[name_key] for v in value]) if name_key else value
    else:
        formatted_value = value

    return '' if formatted_value is False else formatted_value  # empty values are set to False

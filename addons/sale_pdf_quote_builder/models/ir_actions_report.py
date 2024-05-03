# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import io

from PyPDF2 import PdfFileWriter, PdfFileReader
from PyPDF2.generic import NameObject, createStringObject

from odoo import models
from odoo.tools import format_amount, format_date, format_datetime, pdf

from odoo.addons.sale_pdf_quote_builder import utils


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf_prepare_streams(self, report_ref, data, res_ids=None):
        result = super()._render_qweb_pdf_prepare_streams(report_ref, data, res_ids=res_ids)
        if self._get_report(report_ref).report_name != 'sale.report_saleorder':
            return result

        orders = self.env['sale.order'].browse(res_ids)

        for order in orders:
            initial_stream = result[order.id]['stream']
            if initial_stream:
                order_template = order.sale_order_template_id
                header_record = order_template if order_template.sale_header else order.company_id
                footer_record = order_template if order_template.sale_footer else order.company_id
                has_header = bool(header_record.sale_header)
                has_footer = bool(footer_record.sale_footer)
                included_product_docs = self.env['product.document']
                doc_line_id_mapping = {}
                for line in order.order_line:
                    product_product_docs = line.product_id.product_document_ids
                    product_template_docs = line.product_template_id.product_document_ids
                    doc_to_include = (
                        product_product_docs.filtered(lambda d: d.attached_on == 'inside')
                        or product_template_docs.filtered(lambda d: d.attached_on == 'inside')
                    )
                    included_product_docs = included_product_docs | doc_to_include
                    doc_line_id_mapping.update({doc.id: line.id for doc in doc_to_include})

                if (not has_header and not included_product_docs and not has_footer):
                    continue

                all_form_fields = set()
                writer = PdfFileWriter()

                if has_header:
                    self._add_pages_to_writer(
                        writer, base64.b64decode(header_record.sale_header), all_form_fields
                    )
                if included_product_docs:
                    # TODO edm: _get_restricted_form_fields check in case of upgrade? Raise at first found though,
                    #  so maybe not that method, or with a raise=true Though with the upgrade script,
                    #  we could change the param, not the field in the pdf anyway. And it'll crash
                    # TODO edm: raise for all documents or skip the one?
                    # TODO edm: check on header/footer too
                    for doc in included_product_docs:
                        sol_id = doc_line_id_mapping[doc.id]
                        self._add_pages_to_writer(
                            writer, base64.b64decode(doc.datas), all_form_fields, sol_id,
                        )
                self._add_pages_to_writer(writer, initial_stream.getvalue())
                if has_footer:
                    self._add_pages_to_writer(
                        writer, base64.b64decode(footer_record.sale_footer), all_form_fields
                    )

                form_fields = self._get_form_fields_mapping(order, all_form_fields)
                pdf.fill_form_fields_pdf(writer, form_fields=form_fields)
                with io.BytesIO() as _buffer:
                    writer.write(_buffer)
                    stream = io.BytesIO(_buffer.getvalue())
                result[order.id].update({'stream': stream})

        return result

    def _add_pages_to_writer(self, writer, document, all_form_fields=None, sol_id=None):
        # TODO edm: docstring
        prefix = f'sol_id_{sol_id}__' if sol_id else ''
        reader = PdfFileReader(io.BytesIO(document), strict=False)

        field_names = set()
        if all_form_fields != None:
            field_names = reader.getFields()
            if field_names:
                all_form_fields.update([prefix + field for field in field_names])

        for page_id in range(0, reader.getNumPages()):
            page = reader.getPage(page_id)
            if all_form_fields and field_names and sol_id and page.get('/Annots'):
                # Prefix all form fields in the product document with the sale order line id.
                # This is necessary to avoid conflicts between fields with the same name.
                for j in range(0, len(page['/Annots'])):
                    reader_annot = page['/Annots'][j].getObject()
                    if reader_annot.get('/T') in field_names:
                        reader_annot.update({
                            NameObject("/T"): createStringObject(prefix + reader_annot.get('/T'))
                        })
            writer.addPage(page)

    def _get_form_fields_mapping(self, order, all_form_fields):
        """ Dictionary mapping specific pdf fields name to Odoo fields data for a sale order.
        Override this method to add new fields to the mapping.

        :param recordset order: sale.order record
        :rtype: dict
        :return: mapping of fields name to Odoo fields data

        Note: order.ensure_one()
        """
        order.ensure_one()
        env = self.with_context(use_babel=True).env
        tz = order.partner_id.tz or self.env.user.tz or 'UTC'
        lang_code = order.partner_id.lang or self.env.user.lang
        form_fields_mapping = {
            field: utils._get_field_format(field, order, env, tz, lang_code)
            for field in all_form_fields
        }

        return form_fields_mapping

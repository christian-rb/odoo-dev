# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.http import request, content_disposition


def _get_zip_headers(content, filename):
    return [
        ('Content-Type', 'zip'),
        ('X-Content-Type-Options', 'nosniff'),
        ('Content-Length', len(content)),
        ('Content-Disposition', content_disposition(filename)),
    ]


class AccountDocumentDownloadController(http.Controller):

    @http.route('/account/export_invoice_documents/<invoice_ids>', type='http', auth='user')
    def export_invoices_legal_documents(self, invoice_ids, only_pdf=False, attachment_ids=None, filename=None):
        def char_to_list(char_list):
            return [int(i) for i in char_list.split(',')]

        invoices = request.env['account.move'].browse(char_to_list(invoice_ids))
        invoices.check_access_rights('read')
        invoices.check_access_rule('read')
        if attachment_ids:
            attachments = request.env['ir.attachment'].browse(char_to_list(attachment_ids))
        else:
            attachments = invoices._get_invoice_legal_documents(only_pdf=only_pdf)
        attachments.check_access_rights('read')
        attachments.check_access_rule('read')

        if len(attachments) == 1:
            filename = filename or invoices._get_invoice_report_filename()
            headers = {
                'Content-Type': attachments.mimetype,
                'Content-Length': len(attachments.raw),
                'Content-Disposition': content_disposition(filename),
            }
            return request.make_response(attachments.raw, list(headers.items()))
        else:
            filename = filename or (invoices._get_invoice_report_filename(extension='zip') if len(invoices) == 1 else _('invoices') + '.zip')
            content = attachments._build_zip_from_attachments()
            headers = _get_zip_headers(content, filename)
            return request.make_response(content, headers)

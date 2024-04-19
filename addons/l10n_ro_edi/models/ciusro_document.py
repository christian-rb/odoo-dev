# Part of Odoo. See LICENSE file for full copyright and licensing details.

import io
import requests
import zipfile

from lxml import etree
from odoo import models, fields, api, _
from odoo.exceptions import UserError

NS_UPLOAD = {"ns": "mfp:anaf:dgti:spv:respUploadFisier:v1"}
NS_STATUS = {"ns": "mfp:anaf:dgti:efactura:stareMesajFactura:v1"}
NS_HEADER = {"ns": "mfp:anaf:dgti:efactura:mesajEroriFactuta:v1"}
NS_SIGNATURE = {"ns": "http://www.w3.org/2000/09/xmldsig#"}


class CIUSRODocument(models.Model):
    _name = 'ciusro.document'
    _description = "Document object for tracking CIUS-RO XML sent to E-Factura"
    _order = 'datetime DESC, id DESC'

    move_id = fields.Many2one('account.move', required=True)
    state = fields.Selection(
        selection=[
            ('to_send', 'To send'),
            ('sending', 'Sending'),
            ('sent', 'Sent'),
            ('nok', 'Not OK'),
            ('ok', 'OK'),
            ('error', 'Error'),
        ],
        string='E-Factura State',
        default='to_send',
    )
    attachment_id = fields.Binary(string='E-Factura Attachment')
    datetime = fields.Datetime()
    message = fields.Char()
    key_loading = fields.Char()
    key_download = fields.Char()
    key_signature = fields.Char()
    key_certificate = fields.Char()

    @api.model_create_multi
    def create(self, vals_list):
        documents = super().create(vals_list)
        for document in documents:
            document.move_id.l10n_ro_edi_document_ids |= document
            document.move_id.l10n_ro_edi_active_document_id = document
        return documents

    def _get_attachment_file_name(self):
        self.ensure_one()
        return f"{self.move_id.name.replace('/', '_')}_{self.id}.zip"

    def _handle_error(self, message: str):
        self.state = 'error'
        self.message = message

    def _make_request(self, endpoint, xml_data=None, session=None):
        """ Make an API request to E-Factura and return the response
        :param endpoint: 'upload' (for sending, requires xml_data) |
                         'stareMesaj' (for fetching status) |
                         'descarcare' (for downloading answer)
        :return: response from E-Factura
        """
        self.ensure_one()
        self.datetime = fields.Datetime.now()
        self.move_id.l10n_ro_edi_active_document_id = self

        url = f"https://api.anaf.ro/test/FCTEL/rest/{endpoint}"
        headers = {'Content-Type': 'application/xml',
                   'Authorization': f'Bearer {self.move_id.company_id.l10n_ro_edi_access_token}'}

        match endpoint:
            case 'upload':
                if not xml_data:
                    return self._handle_error(_('CIUS-RO XML not found'))
                method = 'POST'
                params = {'standard': 'UBL' if self.move_id.move_type == 'out_invoice' else 'CN',
                          'cif': self.move_id.company_id.vat.replace('RO', '')}
                data = xml_data
            case 'stareMesaj':
                method = 'GET'
                params = {'id_incarcare': self.key_loading}
                data = None
            case 'descarcare':
                method = 'GET'
                params = {'id': self.key_download}
                data = None
            case _:
                raise UserError(_('Invalid request endpoint "%s"') % endpoint)

        try:
            if session:
                response = session.request(method=method, url=url, params=params, data=data, headers=headers, timeout=10)
            else:
                response = requests.request(method=method, url=url, params=params, data=data, headers=headers, timeout=10)
        except requests.HTTPError as e:
            return self._handle_error(str(e))
        if response.status_code == 400:
            error_json = response.json()
            return self._handle_error(error_json['message'])
        if response.status_code == 403:
            return self._handle_error(_('Access token is forbidden'))

        return response

    def _request_ciusro_send_invoice(self, xml_data):
        self.ensure_one()
        response = self._make_request('upload', xml_data)
        if not response:
            return

        root = etree.fromstring(response.content)
        res_status = root.get('ExecutionStatus')
        if res_status == '1':
            error_elements = root.findall('.//ns:Errors', namespaces=NS_UPLOAD)
            error_messages = [error_element.get('errorMessage') for error_element in error_elements]
            return self._handle_error('\n'.join(error_messages))
        else:
            self.state = 'sending'
            self.key_loading = root.get('index_incarcare')

    def _request_ciusro_fetch_status(self, session=None):
        self.ensure_one()
        response = self._make_request('stareMesaj', session=session)
        if not response:
            return

        root = etree.fromstring(response.content)
        error_elements = root.findall('.//ns:Errors', namespaces=NS_STATUS)
        if error_elements:
            error_messages = [error_element.get('errorMessage') for error_element in error_elements]
            return self._handle_error('\n'.join(error_messages))

        state_status = root.get('stare')
        self.key_download = root.get('id_descarcare')
        if state_status in ('nok', 'ok'):
            self.state = state_status

    def _request_ciusro_download_answer(self):
        self.ensure_one()
        response = self._make_request('descarcare')
        if not response:
            return

        # E-Factura gives download response in ZIP format
        zip_ref = zipfile.ZipFile(io.BytesIO(response.content))
        signature_file = next(file for file in zip_ref.namelist() if 'semnatura' in file)

        xml_content = zip_ref.open(signature_file)
        root = etree.parse(xml_content)
        error_element = root.find('.//ns:Error', namespaces=NS_HEADER)
        self.key_signature = root.find('.//ns:SignatureValue', namespaces=NS_SIGNATURE).text
        self.key_certificate = root.find('.//ns:X509Certificate', namespaces=NS_SIGNATURE).text
        if error_element is not None:
            error_message = error_element.get('errorMessage')
            return self._handle_error(error_message)

        self.env['ir.attachment'].create({
            'name': self._get_attachment_file_name(),
            'raw': response.content,
            'mimetype': 'application/zip',
            'res_model': self._name,
            'res_id': self.id,
            'res_field': 'attachment_id',
        })
        self.invalidate_recordset(fnames=['attachment_id'])
        self.state = 'sent'
        # Delete all previous error documents
        to_delete_documents = self.env['ciusro.document'].filtered(lambda d: d.move_id == self.move_id and d.id != self.id)
        to_delete_documents.unlink()

    def action_l10n_ro_edi_fetch_status(self):
        """ Fetch the latest response from E-Factura about the XML sent """
        self.ensure_one()
        if self.state != 'sending':
            raise UserError(_('This document is not currently in sending state'))
        if not self.key_loading:
            raise UserError(_('This document does not have a loading key'))
        self._request_ciusro_fetch_status()

    def action_l10n_ro_edi_download_answer(self):
        """ Download the answer from E-Factura """
        self.ensure_one()
        if self.state not in ('nok', 'ok'):
            raise UserError(_('This document has not received an answer yet'))
        if not self.key_download:
            raise UserError(_('This document does not have a download key'))
        self._request_ciusro_download_answer()

    def action_l10n_ro_edi_download_zip(self):
        """ Download the received ZIP file from E-Factura """
        self.ensure_one()
        if not self.attachment_id:
            raise UserError(_('This document does not have any attachment'))
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/ciusro.document/{self.id}/attachment_id/{self._get_attachment_file_name()}?download=true',
        }

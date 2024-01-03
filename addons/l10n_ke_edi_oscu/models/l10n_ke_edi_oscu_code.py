# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models

URL = "https://etims-api-sbx.kra.go.ke/etims-api/"
CODE_SEARCH_URL = URL + "selectCodeList"

_logger = logging.getLogger(__name__)

CODE_TYPES = [
    ('04', 'Taxation Type'),
    ('05', 'Country'),
    ('07', 'Payment Type'),
    ('09', 'Branch Status'),
    ('10', 'Quantity Unit'),
    ('11', 'Sale Status'),
    ('12', 'Stock I/O Type'),
    ('14', 'Transaction Type'),
    ('17', 'Packing Unit'),
    ('24', 'Item Type'),
    ('26', 'Import Item Status'),
    ('32', 'Refund Reason'),
    ('33', 'Currency'),
    ('34', 'Purchase Status'),
    ('35', 'Reason of Inventory Adjustment'),
    ('36', 'Bank'),
    ('37', 'Sales Receipt Type'),
    ('38', 'Purchase Receipt Type'),
    ('45', 'Tax Office'),
    ('48', 'Locale'),
    ('49', 'Category Level'),
]

class L10nKeOSCUCode(models.Model):
    _name = 'l10n_ke_edi_oscu.code'

    _rec_names_search = ['code', 'name', 'description']

    code_type = fields.Selection(selection=CODE_TYPES, required=True)
    code = fields.Char(required=True)
    name = fields.Char(required=True)
    description = fields.Char()
    active = fields.Boolean(default=True)
    order = fields.Integer()

    tax_rate = fields.Float()

    def _create_vals_from_json(self, json_content):  # TODO - rename to something like '_field_vals_from_json' or '_fields_from_json' since these values aren't always used for creating records
        """ Create codes from the standard json output

        :param dict json_content: the "data" from the selectCodeList query to the device.
        :returns: a list of dicts, can be used to create a recordset of the codes from the parsed data.
        """
        codes_to_create = []
        code_type_specific_fields = {
            # i.e. When cdCls is '04', update the value of the field 'tax_rate' with the value of 'userDfnCd1' cast as a float
            '04': [('tax_rate', float)],
        }
        code_types_in_use = [num for num, _desc in self._fields['code_type'].selection]
        print(json_content) # TODO - remove all print statements, perhaps replace them with
        #                            appropriate DEBUG-level logging
        for code_data in json_content['clsList']:
            code_type = code_data['cdCls']
            if code_type not in code_types_in_use:
                continue
            code_list = code_data['dtlList']
            codes_to_create += [{
                'code_type': code_type,
                'code': code['cd'],
                'name': code['cdNm'],
                'description': code['cdDesc'],
                'active': True if code['useYn'] == 'Y' else False,
                'order': int(code['srtOrd']),
                # TODO - I overcomplicated this, unless we can find another few codes for which a
                #        userDfnCd field needs to be written to a field on the code model, this
                #        should probably just be simplified to a more readable series of if
                #        conditions (i.e. if code type == '04' then write the content of userDfnCd1
                #        to the 'tax_rate' field)
                **{
                    name: transform(code[correlate]) for
                    (name, transform), correlate in
                    zip(
                        code_type_specific_fields.get(code_type, []),
                        ['userDfnCd1', 'userDfnCd2', 'userDfnCd3']
                    )
                }
            } for code in code_list]

        return codes_to_create

    def _create_or_update_from_vals(self, create_vals):
        """ Update existing records, or create new ones depending on whether the code exists

        :param list[dict] create_vals: list of l10n_ke_edi_oscu.code creation vals.
        :returns: tuple consisting of a recordset of created codes and a recordset of updated codes.
        """
        codes = self.with_context(active_test=False).search([])
        existing_code_details = {(rec.code_type, rec.code): rec.id for rec in codes}
        to_create = []
        updated_codes = self

        for val in create_vals:
            if code_id := existing_code_details.get((val['code_type'], val['code'])):
                to_update = self.browse(code_id)
                to_update.write(val)
                updated_codes |= to_update
            else:
                to_create.append(val)

        created = self.create(to_create)
        model_data_values = [
            {
                "name": "code_" + code.code_type + "_" + code.code,
                "model": "l10n_ke_edi_oscu.code",
                "module": "l10n_ke_edi_oscu",
                "res_id": code.id,
                "noupdate": True,
            }
            for code in created
        ]
        if model_data_values:
            self.env['ir.model.data'].create(model_data_values)

        return created, updated_codes

    def _cron_get_codes_from_device(self):
        """ Automatically fetch, and create or update codes from the KRA, using the endpoint on the device """
        company = self.env['res.company'].search([('l10n_ke_oscu_is_active', '=', True)], limit=1)
        if not company:
            _logger.error('No OSCU initialized company could be found. No KRA Codes fetched.')
            return

        # The API will return all codes added since this date
        last_request_date = self.env['ir.config_parameter'].get_param('l10n_ke_oscu.last_code_request_date', '20180101000000')
        error, data, _date = company._l10n_ke_call_etims('selectCodeList', {'lastReqDt': last_request_date})
        if error:
            if error['code'] == '001':
                _logger.info("No new KRA standard codes fetched from the OSCU.")
                return
            _logger.error('Request Error [%s]: %s', error['code'], error['message'])
        created, updated = self.sudo()._create_or_update_from_vals(self._create_vals_from_json(data))
        _logger.info("Fetched KRA standard codes from the OSCU, created %i and updated %i.", len(created), len(updated))
        self.env['ir.config_parameter'].sudo().set_param('l10n_ke_oscu.last_code_request_date', fields.Datetime.now().strftime('%Y%m%d%H%M%S'))
        return

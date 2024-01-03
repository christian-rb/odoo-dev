# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import requests
from collections import defaultdict

from odoo import _, api, Command, fields, models
from odoo.addons.base.models.ir_qweb_fields import Markup
from odoo.tools.float_utils import json_float_round
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    # TODO - reconcile field naming convention (same problem throughout, in account move etc)
    #      - help strings for fields that appear on the product view
    l10n_ke_packaging_unit_id = fields.Many2one(
        'l10n_ke_edi_oscu.code',
        related='product_variant_ids.l10n_ke_packaging_unit_id',
        readonly=False, string='Packaging Unit',
        domain=[('code_type', '=', '17')],
        help='KRA code that describes the type of packaging used.',
        copy=True,
    )
    l10n_ke_packaging_quantity = fields.Float(
        string='Package Quantity',
        related='product_variant_ids.l10n_ke_packaging_quantity',
        readonly=False, default=1,
        copy=True,
    )
    l10n_ke_origin_country_id = fields.Many2one(
        'res.country',
        related='product_variant_ids.l10n_ke_origin_country_id',
        readonly=False, string='Origin Country',
        copy=True,
    )
    l10n_ke_tax_type_code = fields.Char(related='product_variant_ids.l10n_ke_tax_type_code')
    l10n_ke_unspsc_type_code = fields.Char(related='product_variant_ids.l10n_ke_unspsc_type_code')
    l10n_ke_product_type_code = fields.Selection(
        related='product_variant_ids.l10n_ke_product_type_code',
        readonly=False,
        copy=True,
    )
    l10n_ke_is_insurance_applicable = fields.Boolean(
        related='product_variant_ids.l10n_ke_is_insurance_applicable',
        readonly=False,
        copy=True,
    )
    l10n_ke_item_code = fields.Char(string="KRA Item Code", related='product_variant_ids.l10n_ke_item_code')

    def action_l10n_ke_oscu_save_item(self):
        if self.product_variant_count != 1:
            raise UserError
        return self.product_variant_ids.action_l10n_ke_oscu_save_item()

    def action_l10n_ke_oscu_save_stock_master(self):
        if self.product_variant_count != 1:
            raise UserError
        return self.product_variant_ids.action_l10n_ke_oscu_save_stock_master()

    # OVERRIDE
    def _get_related_fields_variant_template(self):
        return [
            *super()._get_related_fields_variant_template(),
            'l10n_ke_packaging_unit_id',
            'l10n_ke_packaging_quantity',
            'l10n_ke_origin_country_id',
            'l10n_ke_product_type_code',
            'l10n_ke_is_insurance_applicable',
        ]


class ProductProduct(models.Model):
    _inherit = 'product.product'

    l10n_ke_packaging_unit_id = fields.Many2one(
        'l10n_ke_edi_oscu.code',
        string='Packaging Unit',
        domain=[('code_type', '=', '17')],
        compute='_compute_l10n_ke_packaging_unit_id',
        store=True, readonly=False,
        help='KRA code that describes the type of packaging used.',
    )
    l10n_ke_packaging_quantity = fields.Float(
        string='Package Quantity',
        help='Number of products in a package.',
        default=1,
    )

    l10n_ke_origin_country_id = fields.Many2one(
        'res.country',
        readonly=False,
        string='Origin Country',
        help='The origin country of the product.'
    )
    l10n_ke_tax_type_code = fields.Char(compute='_compute_l10n_ke_tax_type_code')
    l10n_ke_unspsc_type_code = fields.Char("UNSPSC Code Tax Type", related='unspsc_code_id.l10n_ke_tax_type_id.code')
    l10n_ke_product_type_code = fields.Selection(
        string="Product Type",
        selection=[('1', 'Raw Material'), ('2', 'Finished Product'), ('3', 'Service')],
        help="Used by eTIMS to determine the type of the product",
    )
    l10n_ke_is_insurance_applicable = fields.Boolean(string='Insurance Applicable')
    l10n_ke_item_code = fields.Char('Item Code', readonly=True)

    @api.depends('taxes_id.l10n_ke_tax_type_id')
    def _compute_l10n_ke_tax_type_code(self):
        for product in self:
            tax_codes = product.taxes_id.mapped("l10n_ke_tax_type_id")
            product.l10n_ke_tax_type_code = tax_codes[0].code if tax_codes else ''

    @api.depends('detailed_type')
    def _compute_l10n_ke_packaging_unit_id(self):
        """ Assign a value to the packaging unit by default, based on the type of product it is. """
        service_packaging = self.env.ref('l10n_ke_edi_oscu.packaging_type_ou', raise_if_not_found=False)
        for product in self.filtered(lambda p: not p.l10n_ke_packaging_unit_id):
            product.l10n_ke_packaging_unit_id = service_packaging if product.detailed_type == 'service' else None

    def _calculate_l10n_ke_item_code(self):
        """ Computes the item code of a given product

        For instance KE1NTXU is an item code, where
        KE:      first two digits are the origin country of the product
        1:       the product type (raw material)
        NT:      the packaging type
        XU:      the quantity type
        0000006: a unique value (id in our case)
        """
        code_fields = [
            self.l10n_ke_origin_country_id.code,
            self.l10n_ke_product_type_code,
            self.l10n_ke_packaging_unit_id.code,
            self.uom_id.l10n_ke_quantity_unit_id.code,
        ]
        if not all(code_fields):
            self.l10n_ke_item_code = ''
            return ''

        item_code_prefix = ''.join(code_fields)
        return item_code_prefix + \
            ('0'*20)[:-len(item_code_prefix)-len(str(self.id))] + \
            str(self.id)

    def _l10n_ke_oscu_save_item_content(self):
        """ When saving an item to the OSCU, these are the required fields. """
        self.ensure_one()
        code = self.l10n_ke_item_code or self._calculate_l10n_ke_item_code()
        content = {
            'itemCd':      code,                                                 # Item Code
            'itemClsCd':   self.unspsc_code_id.code or '',                       # HS Code (unspsc format)
            'itemTyCd':    self.l10n_ke_product_type_code,                       # Generally raw material, finished product, service
            'itemNm':      self.name,                                            # Product name
            'orgnNatCd':   self.l10n_ke_origin_country_id.code,                  # Origin nation code
            'pkgUnitCd':   self.l10n_ke_packaging_unit_id.code,                  # Packaging unit code
            'qtyUnitCd':   self.uom_id.l10n_ke_quantity_unit_id.code,            # Quantity unit code
            'taxTyCd':     self.l10n_ke_tax_type_code,                           # Tax type code
            'bcd':         self.barcode or None,                                 # Self barcode
            'dftPrc':      self.standard_price,                                  # Standard price
            'isrcAplcbYn': 'Y' if self.l10n_ke_is_insurance_applicable else 'N', # Is insurance applicable
            'useYn':'Y',
            **self.env.company._l10n_ke_get_user_dict(self.create_uid, self.write_uid),
        }
        return content

    def _l10n_ke_oscu_save_item(self):
        content = self._l10n_ke_oscu_save_item_content()
        error, data, date = self.env.company._l10n_ke_call_etims('saveItem', content)
        if not error:
            self.l10n_ke_item_code = content['itemCd']
        return error, content

    def action_l10n_ke_oscu_save_item(self):
        """Register the item with the OSCU.

        Regstration allows the product to be used via its itemCd in other requests such as invoice
        and stock move reporting.
        """
        validation_messages = self._l10n_ke_get_validation_messages(is_invoice=False)
        if validation_messages.get('blocking'):
            raise UserError(_("Cannot register '%s' on eTIMS:\n%s", self.name, validation_messages['message']))
        error, content = self._l10n_ke_oscu_save_item()
        if error:
            raise UserError("[" + error['code'] + "] " + error['message']) # TODO fstring this instead
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'sticky': False,
                'message': _("Product successfully registered"),
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    @api.model
    def _l10n_ke_oscu_find_product_from_json(self, product_dict):
        """ Find a product matching that of a given product represented json format provided by the API

        :param dict product_dict: dictionary representing the fields of the product as obtained from
                                  the API.
        :returns:                 a tuple, containing a product (or None type) that is strongest
                                  match to an item with the given details, and a message if
                                  describing the method by which the matching that was accomplished.
        """
        if product_dict.get('bcd'):
            search_domain = [('barcode', '=', product_dict['bcd']), ('unspsc_code_id.code', '=', product_dict['itemClsCd'])]
            if (product := self.search(search_domain, limit=1)):
                return product, _('"%s" matched using an exact matching of barcode and UNSPSC code.', product.name)
            else:
                return None, _(
                    '"%s" could not be matched to any product, since it has a barcode (%s) and UNSPSC'
                    'code (%s) that do not match any existing product.',
                    product_dict['itemNm'], product_dict['bcd'], product_dict['itemClsCd'],
                )

        if (product := self.search([
            ('unspsc_code_id.code', '=', product_dict['itemClsCd']),
            ('name', 'ilike', product_dict['itemNm'])
        ], limit=1)):
            return product, _('"%s" matched using an exact matching of name and UNSPSC code.', product.name),

        fuzzy_name = ('name', 'ilike', f"%{'%'.join(product_dict['itemNm'].split())}%")
        search_domain = [('unspsc_code_id.code', '=', product_dict['itemClsCd']), fuzzy_name]
        if (product := product_dict.get('itemClsCd') and self.search(search_domain, limit=1)):
            return product, _(
                '"%s" matched using an inexact matching of name and an exact matching of UNSPSC code.',
                product.name
            )

        return None, _('The product "%s" with UNSPSC code: "%s" could not be matched to any existing product.', product_dict['itemNm'], product_dict['itemClsCd'])

    @api.model
    def _l10n_ke_assign_products_from_json(self, lines_dict):
        """ Using the info from the JSON, update the given item with a product id.

        :param dict lines_dict: dictionary of the form 'itemSeq': item where item is a JSON
                                dictionary representing the fields of the product as obtained from
                                the API.
        :returns:               lines_dict, with values updated in place.
        """
        product_map = {}
        for item_seq, item in lines_dict.items():
            key_fields = tuple(item[field] for field in ('itemNm', 'bcd', 'itemClsCd'))
            if key_fields in product_map:
                item['product'] = product_map[key_fields]
                continue

            product_dict = {key: val for key, val in zip(('itemNm', 'bcd', 'itemClsCd'), key_fields)}
            product, message = self._l10n_ke_oscu_find_product_from_json(product_dict)
            if (product or message):
                product_map[key_fields] = product
                item.update({
                    'product': product,
                    'message': message,
                    'uom_id': product.uom_id.id if product else False,
                    'uom_code': product.uom_id.l10n_ke_quantity_unit_id.code if product else False,
                })
                continue

        return lines_dict

    def _l10n_ke_get_validation_messages(self, is_invoice=False):
        """ Get the warning messages associated with the products.

        :param bool is_invoice: whether the message should mention that the cost is required for the
            product.
        :returns: a dictionary, containing the message, an associated action and a name
            for the action.
        """
        misconfigured_products = self.filtered(
            lambda p: not p.unspsc_code_id or not p.l10n_ke_packaging_unit_id
            or not p.l10n_ke_packaging_quantity
            or (not is_invoice and (not p.standard_price or not p.l10n_ke_origin_country_id or not p.l10n_ke_product_type_code))
        )

        message = {
            False: _(
                "When sending to eTIMS, the products used must have a defined Cost, Product Type, "
                "Origin Country, Packaging Unit, Packaging Quantity and UNSPSC Code."
            ),
            True: _(
                "When sending to eTIMS, the products used must have a defined Packaging Unit, "
                "Packaging Quantity and UNSPSC Code."
            ),
        }[is_invoice]

        return {
            'message': message,
            'action_text': _("View Product(s)"),
            'action': self._l10n_ke_action_open_products(misconfigured_products.ids),
            'blocking': True,
        } if misconfigured_products else {}

    def _l10n_ke_action_open_products(self, res_ids, title=None): #TODO - docstring
        if not isinstance(res_ids, tuple | list):
            res_ids = [res_ids]
        res = {
            'name': title or _("Products"),
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'domain': [('id', 'in', res_ids)],
            'view_mode': 'tree',
            'views': [(self.env.ref('l10n_ke_edi_oscu.l10n_ke_kra_product_tree').id, 'tree'), (False, 'form')],
            'context': {'create': False, 'delete': False},
        }
        return res

class ProductCode(models.Model):

    _inherit = 'product.unspsc.code'

    l10n_ke_special = fields.Boolean()
    l10n_ke_tax_type_id = fields.Many2one('l10n_ke_edi_oscu.code')

    def _cron_l10n_ke_oscu_get_codes_from_device(self):
        """ Automatically fetch and create UNSPSC codes from the OSCU if they don't already exist """
        company = self.env['res.company'].search([
            ('l10n_ke_oscu_is_active', '=', True),
        ], limit=1)
        if not company:
            _logger.error('No OSCU initialized company could be found. No KRA Codes fetched.')
            return

        tax_codes = {
            tax_code['code']: tax_code['id'] for
            tax_code in self.env['l10n_ke_edi_oscu.code'].search_read([('code_type', '=', '04')], ['code'])
        }
        last_request_date = self.env['ir.config_parameter'].get_param('l10n_ke_oscu.last_unspsc_code_request_date', '20180101000000')
        error, data, _date = company._l10n_ke_call_etims('selectItemClsList', {'lastReqDt': last_request_date})
        if error:
            if error.get('code') == '001':
                _logger.info("No new UNSPSC codes fetched from the OSCU.")
                return
            raise UserError(f"[{error['code']}] {error['message']}")

        cls_list = {item['itemClsCd']: item for item in data['itemClsList']}
        existing_codes = self.search([
            ('code', 'in', list(cls_list.keys()))
        ])
        for code in existing_codes:
            if (new_tax_code :=  not code.l10n_ke_tax_type_id and cls_list[code.code]['taxTyCd']):
                code.write({'l10n_ke_tax_type_id': tax_codes.get(new_tax_code)})

        new_codes = self.env['product.unspsc.code'].create([{
            'name': code_dict['itemClsNm'],
            'code': code,
            'applies_to': 'product',
            'l10n_ke_special': True,
            'l10n_ke_tax_type_id': tax_codes.get(code_dict['taxTyCd']),
        } for code, code_dict in cls_list.items() if code not in existing_codes.mapped('code')])

        _logger.info("%i UNSPSC codes fetched from the OSCU, %i UNSPSC codes created", len(cls_list), len(new_codes))
        self.env['ir.config_parameter'].sudo().set_param('l10n_ke_oscu.last_unspsc_code_request_date', fields.Datetime.now().strftime('%Y%m%d%H%M%S'))
        return

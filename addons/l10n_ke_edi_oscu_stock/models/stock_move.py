# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json

from markupsafe import Markup
from collections import defaultdict

from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import json_float_round
from odoo.tools import groupby

URL = "https://etims-api-sbx.kra.go.ke/etims-api/"
SAVE_STOCK_IO_URL = URL + "insertStockIO"
FETCH_STOCK_MOVE_URL = URL + ""


class StockMove(models.Model):
    _inherit = "stock.move"

    l10n_ke_oscu_flow_type_code = fields.Selection(
        selection=[
            ('01', 'Import Incoming'),
            ('02', 'Purchase Incoming'),
            ('03', 'Return Incoming'),
            ('04', 'Stock Movement Incoming'),
            ('05', 'Processing Incoming'),
            ('06', 'Adjustment Incoming'),
            ('11', 'Sale Outgoing'),
            ('12', 'Return Outgoing'),
            ('13', 'Stock Movement Outgoing'),
            ('14', 'Processing Outgoing'),
            ('15', 'Discarding Outgoing'),
            ('16', 'Adjustment Outgoing'),
        ],
        compute='_compute_l10n_ke_oscu_flow_type_code',
        string="eTIMS Category",
        store=True, readonly=False, copy=False,
    )
    l10n_ke_oscu_sar_number = fields.Integer(
        string='Store and Release Number',
        copy=False,
        help="Number used by the KRA to identify stock movements",
    )
    country_code = fields.Char(related='company_id.account_fiscal_country_id.code')

    @api.depends('location_id.usage', 'location_dest_id.usage', 'partner_id')
    def _compute_l10n_ke_oscu_flow_type_code(self):
        flow_mappings = {
            # Partner type, location_id.usage, location_dest_id.usage
            ('external', 'supplier',    'internal'  ): '02', # Purchase Incoming
            (False, 'customer',    'internal'  ): '03', # Return Incoming
            ('branch', 'supplier',    'internal'  ): '04', # Stock Move Incoming
            (False, 'production',  'internal'  ): '05', # Processing Incoming
            (False, 'inventory',   'internal'  ): '06', # Adjustment Incoming
            (False, 'supplier', 'internal'): '06',
            ('external', 'internal',    'customer'  ): '11', # Sale Outgoing
            (False, 'internal',    'supplier'  ): '12', # Return Outgoing
            ('branch', 'internal',    'customer'  ): '13', # Stock Move Outgoing
            (False, 'internal',    'production'): '14', # Processing Outgoing
            (False, 'internal', 'customer'): '16',  # Adjustment Outgoing
            (False, 'internal',    'inventory' ): '16', # Adjustment Outgoing
        }
        ke_moves = self.filtered(lambda m: m.company_id.country_id.code == "KE")
        (self - ke_moves).l10n_ke_oscu_flow_type_code = False

        for move in ke_moves:
            if move.scrapped:
                move.l10n_ke_oscu_flow_type_code = '15'      # Discarding Outgoing
                continue

            partner_type = 'internal'
            if partner := move.picking_id.partner_id:
                company = self.env['res.company'].search([('partner_id', '=', partner.id)], limit=1)
                partner_type = 'branch' if company and company.country_code == 'KE' else 'external'

            code = flow_mappings.get((
                partner_type, move.location_id.usage, move.location_dest_id.usage
            )) or flow_mappings.get((False, move.location_id.usage, move.location_dest_id.usage))
            if code == '02' and move.picking_id.partner_id.country_id.code not in ['KE', False]:
                code = '01'
            move.l10n_ke_oscu_flow_type_code = code

    # STOCK IO
    def _calculate_unit_cost(self):
        """ For stockable products we can easily use the stock valuation layers to calculate the unit price"""
        self.ensure_one()
        unit_price = 0
        quantity_product_uom = self.product_uom._compute_quantity(self.quantity, self.product_id.uom_id)
        for layer in self.stock_valuation_layer_ids:
            unit_price += layer.unit_cost * (quantity_product_uom / layer.quantity)
        return unit_price

    def _l10n_ke_oscu_get_stock_io_content(self):
        items = []
        for index, move in enumerate(self):
            product = move.product_id # for ease of use
            taxes = product.taxes_id.filtered(lambda tax: tax.l10n_ke_tax_type_id)
            tax_rate = (taxes[0].amount / 100) if taxes else 0
            quantity_product_uom = move.product_uom._compute_quantity(move.quantity, move.product_id.uom_id)

            # but get from product for now
            price = abs(move._calculate_unit_cost()) * (move.quantity / quantity_product_uom)
            price = price or move.product_id.standard_price # Suppose the user forgot to set it
            base_amount = quantity_product_uom * price

            item = {
                'itemSeq':   index + 1,
                'itemCd':    product.l10n_ke_item_code,                    # Item code (if it's there)
                'itemClsCd': product.unspsc_code_id.code,                  # UNSPSC Code
                'itemNm':    product.name,                                 # Product name
                'bcd':       product.barcode if product.barcode else '', # Barcode
                'pkgUnitCd': product.l10n_ke_packaging_unit_id.code,       # Packaging unit code
                'pkg':       json_float_round(quantity_product_uom / product.l10n_ke_packaging_quantity, 2),           # Packaging quantity
                'qtyUnitCd': move.product_uom.l10n_ke_quantity_unit_id.code, # UoM (but as defined by Kenya)
                'qty':       json_float_round(move.quantity, 2),                             # Quantity
                'prc':       json_float_round(price, 2),                              # Unit price cost
                'splyAmt':   json_float_round(base_amount, 2),                                  # Cost of items
                'totDcAmt':  0,                                            # Total discount amount
                'taxblAmt':  json_float_round(base_amount, 2),                                  # Taxable amount
                'taxTyCd':   product.l10n_ke_tax_type_code,                          # Tax type code
                'taxAmt':    json_float_round(base_amount * tax_rate, 2),            # Tax amount
                'totAmt':    json_float_round(base_amount * (1 + tax_rate), 2)       # Total amount
            }
            items.append(item)
        return items

    def _l10n_ke_oscu_save_stock_io_content(self):
        """The self being sent should have the same done date."""
        first_move = self[0]
        customer_info = {
            'custTin':                  first_move.partner_id.vat or None,   # Customer TIN
            'custNm':                   first_move.partner_id.name or None,  # Customer Name
            'custBhfId':                first_move.partner_id.l10n_ke_oscu_branch_code or None, # Customer Branch ID
        }
        lines = self._l10n_ke_oscu_get_stock_io_content()
        content = {
            **customer_info,
            'regTyCd':                  'M',                                         # Registration type code # TODO (if this becomes automatic, then A)
            'sarTyCd':                  first_move.l10n_ke_oscu_flow_type_code,            # Stored and released type code
            'ocrnDt':                   first_move.date.strftime('%Y%m%d'),                # Occurred date
            **self.env.company._l10n_ke_get_user_dict(first_move.create_uid, first_move.write_uid),
            'totItemCnt':               len(self),
            'totTaxblAmt':              json_float_round(sum(float(line['taxblAmt']) for line in lines), 2),
            'totTaxAmt':                json_float_round(sum(float(line['taxAmt']) for line in lines), 2),
            'totAmt':                   json_float_round(sum(float(line['totAmt']) for line in lines), 2),
            'itemList':                 lines,
        }
        return content

    def action_l10n_ke_save_stock_io(self):
        self.ensure_one()
        # Maybe check that not more than one picking is sent
        if self.product_id.type != 'product':
            raise UserError(_('We should only send stockable products'))
        if self.l10n_ke_oscu_sar_number and self.search([('l10n_ke_oscu_sar_number', '=', self.l10n_ke_oscu_sar_number),
                                                         ('id', '!=', self.id)], limit=1): # Avoid sending from here if it was sent with a picking
            raise UserError(_('This has already been sent together with other stock moves. ')) #TODO: button is not available anyways
        if self.product_id._l10n_ke_get_validation_messages() or self.product_uom._l10n_ke_get_validation_messages():
            raise UserError(_('Information is missing on the product or Unit of Measure. '))
        if not self.product_id.l10n_ke_item_code:
            self.product_id.action_l10n_ke_oscu_save_item()

        error, dummy = self._l10n_ke_save_stock_io()
        if error:
            raise UserError(error)

        if not self.search([('id', '!=', self.id),
                            ('product_id', '=', self.product_id.id),
                            ('l10n_ke_oscu_flow_type_code', '!=', False),
                            ('l10n_ke_oscu_sar_number', '=', False),
                            ('date', '>=', self.date),
                            ('company_id', '=', self.company_id.id),
                            ('state', '=', 'done'),
                    ], limit=1):
            self.product_id.action_l10n_ke_oscu_save_stock_master()

    def _l10n_ke_save_stock_io(self):
        content = self._l10n_ke_oscu_save_stock_io_content()
        content.update({
            'sarNo': self.company_id._l10n_ke_get_sar_sequence().next_by_id(),
            'orgSarNo': self[0].picking_id.backorder_id and self[0].picking_id.backorder_id.move_ids[0].id or 0,
        })
        error, dummy, dummy = self.company_id._l10n_ke_call_etims('insertStockIO', content)
        if not error:
            for move in self:
                move.l10n_ke_oscu_sar_number = content['sarNo']
        return error, content

    def _cron_l10n_ke_process_pickings(self):
        companies = self.env.companies.filtered(lambda c: c.l10n_ke_oscu_is_active)

        for company in companies:
            self_company = self.with_context(allowed_company_ids=company.ids)
            self_company._l10n_ke_process_pickings()

    def _action_done(self, cancel_backorder=False):
        res = super()._action_done(cancel_backorder=cancel_backorder)
        if self.filtered(lambda m: m.l10n_ke_oscu_flow_type_code):
            self.env.ref("l10n_ke_edi_oscu_stock.ir_cron_send_stock_moves")._trigger()
        return res

    def _l10n_ke_process_pickings(self):
        """
        This orders the pickings by date and tries to send the entire pickings at once.   If there are
        moves in between, they get sent as well and put in the attachment of the picking after.  The attachment of the
        last picking also gets the ones from the moves after (if there is no later picking yet)

        If some products were not in any picking, but they have been registered before, then those stock moves will be
        sent automatically as well.  If a picking had been sent before, the content is also added in the attachment.

        The goal is to simplify the life of the user.  He could register every product manually and then even send the
        move manually and send the master stock.  Here, however, we allow the user to only bother with eTIMS on the
        picking.  It will show a message when information is missing on the product/UoM in the picking and if those warnings
        have been resolved, the system will automatically send the product registration, the movements and in the end,
        the stock master.
        """
        from_date = self.env['ir.config_parameter'].sudo().get_param('l10n_ke.start_stock_date')
        domain = [
            ('move_ids.l10n_ke_oscu_flow_type_code', '!=', False),
            ('move_ids.l10n_ke_oscu_sar_number', '=', False), # Any should be False...
            ('state', '=', 'done'),
            ('company_id', '=', self.env.company.id),
        ]
        if from_date:
            domain += [('date', '>=', from_date)]
        pickings = self.env['stock.picking'].search(domain, order="date")
        products_picking_done = {}
        products_done = self.env['product.product']
        contents = {}
        for pick in pickings:
            errors = []
            contents[pick] = []
            todo_moves = pick.move_ids.filtered(lambda m: not m.l10n_ke_oscu_sar_number and m.product_id.type == 'product')
            if not todo_moves:
                continue
            # If information is missing, skip the picking
            if pick.l10n_ke_validation_msg:
                continue

            # Keep track of the last picking this product was sent with
            products = todo_moves.mapped('product_id')
            products_done |= products
            for product in products:
                products_picking_done[product] = pick

            # Register products that have not been registered yet
            to_register = todo_moves.mapped('product_id').filtered(lambda p: not p.l10n_ke_item_code)
            for product in to_register:
                error, content = product._l10n_ke_oscu_save_item()
                if error:
                    errors.append(error)
                    continue
                else:
                    contents[pick].append(content)

            #Send the picking itself
            error, content = todo_moves._l10n_ke_save_stock_io()
            if error:
                errors.append(error)
            else:
                contents[pick].append(content)

            unique_errors = list(set([e['code'] + ' ' + e['message'] for e in errors]))
            pick.l10n_ke_error_msg = {
                'message_' + str(i): {
                    'message': error_msg,
                }
                for i, error_msg in enumerate(unique_errors)} # Only show the same error twice
            max_message = len(unique_errors)

        # Link any moves left to the last picking if there is any
        domain = [('product_id.l10n_ke_item_code', '!=', False),
                  ('product_id.type', '=', 'product'),
                  ('state', '=', 'done'),
                  ('picking_id', '=', False),
                  ('l10n_ke_oscu_flow_type_code', '!=', False),
                  ('l10n_ke_oscu_sar_number', '=', False),
                  ('company_id', '=', self.env.company.id)]
        if from_date:
            domain += [('date', '>=', from_date)]
        moves_to_send = self.search(domain, order="date")
        for move in moves_to_send:
            error, content = move._l10n_ke_save_stock_io()
            pick = products_picking_done.get(move.product_id)
            if not error:
                if pick:
                    contents[pick].append(content)
                else:
                    products_done |= move.product_id
                    pick = self.env['stock.picking'].search([
                        ('product_id', '=', move.product_id.id),
                        ('state', '=', 'done'),
                        ('move_ids.l10n_ke_oscu_flow_type_code', '!=', False),
                        ('move_ids.l10n_ke_oscu_sar_number', '!=', False),
                        ('company_id', '=', self.env.company.id)
                    ], order='date desc', limit=1)
                    if pick:
                        contents[pick] = content
                        products_picking_done[move.product_id] = pick

        # Send stock master for all products where we sent all moves (all moves is not really all moves)
        # But calculate the correction qties first

        # Need to find warehouses of the company explicitly separately as Odoobot skips company rules:
        whs = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)])
        _domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self.env['product.product'].with_context(
            warehouse=whs.ids)._get_domain_locations()

        domain = [('product_id', 'in', products_done.ids),
                  ('state', '=', 'done'),
                  ('l10n_ke_oscu_flow_type_code', '!=', False),
                  ('l10n_ke_oscu_sar_number', '=', False),
                  ('company_id', '=', self.env.company.id)]
        domain_move_in = domain + domain_move_in_loc
        domain_move_out = domain + domain_move_out_loc

        data_in = self._read_group(domain_move_in, ['product_id', 'product_uom'], ['quantity:sum'])
        moves_in_res = defaultdict(float)
        for product, product_uom, qty_sum in data_in:
            moves_in_res[product.id] += product_uom._compute_quantity(qty_sum, product.uom_id, round=False)

        data_out = self._read_group(domain_move_out, ['product_id', 'product_uom'], ['quantity:sum'])
        moves_out_res = defaultdict(float)
        for product, product_uom, qty_sum in data_out:
            moves_out_res[product.id] += product_uom._compute_quantity(qty_sum, product.uom_id, round=False)

        for product in products_done:
            pick = products_picking_done.get(product)
            correction_qty = -moves_in_res.get(product.id, 0.0) + moves_out_res.get(product.id, 0.0)
            error, content = product._l10n_ke_save_stock_master(qty_to_add=correction_qty)
            if error:
                if pick and pick in pickings:
                    max_message += 1
                    err_msg = pick.l10n_ke_error_msg
                    err_msg.update({
                        'message_' + str(max_message): {
                            'message': Markup('<br/> %s') % (_('Sending Stock Master:') + error['message'])
                        }
                    })
                    pick.l10n_ke_error_msg = err_msg
            elif pick:
                contents[pick].append(content)

        # add attachments to pickings with the contents we sent
        for pick in contents.keys():
            if content := contents[pick]:
                if pick in pickings:
                    self.env['ir.attachment'].create({
                        'name': 'KRA ' + pick.name + '.json',
                        'res_model': 'stock.picking',
                        'res_id': pick.id,
                        'raw': "\n".join(json.dumps(p, indent=4) for p in content),
                    })
                else:
                    attach = self.env['ir.attachment'].search([
                        ('name', '=', 'KRA ' + pick.name + '.json'),
                        ('res_model', '=', 'stock.picking'),
                        ('res_id', '=', pick.id),
                    ], limit=1)
                    attach.raw = attach.raw + ("\n" + "\n".join(json.dumps(p, indent=4) for p in contents)).encode()

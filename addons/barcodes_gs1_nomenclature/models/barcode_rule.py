from odoo import fields, models


class BarcodeRule(models.Model):
    _inherit = 'barcode.rule'

    def _default_encoding(self):
        return 'gs1-128' if self.env.context.get('is_gs1') else 'any'

    encoding = fields.Selection(
        selection_add=[('gs1-128', 'GS1-128')], default=_default_encoding,
        ondelete={'gs1-128': 'set default'})
    type = fields.Selection(
        selection_add=[
            ('location', 'Location'),
            ('location_dest', 'Destination location'),
            ('lot', 'Lot number'),
            ('package', 'Package'),
            ('use_date', 'Best before Date'),
            ('expiration_date', 'Expiration Date'),
            ('package_type', 'Package Type'),
            ('pack_date', 'Pack Date'),
        ], ondelete={
            'location': 'set default',
            'location_dest': 'set default',
            'lot': 'set default',
            'package': 'set default',
            'use_date': 'set default',
            'expiration_date': 'set default',
            'package_type': 'set default',
            'pack_date': 'set default',
        })
    gs1_content_type = fields.Selection([
        ('date', 'Date'),
        ('measure', 'Measure'),
        ('identifier', 'Numeric Identifier'),
        ('alpha', 'Alpha-Numeric Name'),
    ], string="GS1 Content Type",
        help="The GS1 content type defines what kind of data the rule will process the barcode as:\
        * Date: the barcode will be converted into a Odoo datetime;\
        * Measure: the barcode's value is related to a specific UoM;\
        * Numeric Identifier: fixed length barcode following a specific encoding;\
        * Alpha-Numeric Name: variable length barcode.")
    gs1_decimal_usage = fields.Boolean('Decimal', help="If True, use the last digit of AI to determine where the first decimal is")


class BarcodeRulePart(models.Model):
    _inherit = 'barcode.rule.part'

    type = fields.Selection(
        selection_add=[
            ('location', 'Location'),
            ('location_dest', 'Destination location'),
            ('lot', 'Lot number'),
            ('package', 'Package'),
            ('use_date', 'Best before Date'),
            ('expiration_date', 'Expiration Date'),
            ('package_type', 'Package Type'),
            ('pack_date', 'Pack Date'),
        ], ondelete={
            'location': 'set default',
            'location_dest': 'set default',
            'lot': 'set default',
            'package': 'set default',
            'use_date': 'set default',
            'expiration_date': 'set default',
            'package_type': 'set default',
            'pack_date': 'set default',
        })

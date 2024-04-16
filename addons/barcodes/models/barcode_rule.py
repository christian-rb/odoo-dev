import re

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BarcodeRule(models.Model):
    _name = 'barcode.rule'
    _description = 'Barcode Rule'
    _order = 'sequence asc, id'

    name = fields.Char(string='Rule Name', required=True, help='An internal identification for this barcode nomenclature rule')
    barcode_nomenclature_id = fields.Many2one('barcode.nomenclature', string='Barcode Nomenclature')
    sequence = fields.Integer(string='Sequence', help='Used to order rules such that rules with a smaller sequence match first')
    encoding = fields.Selection(
        string='Encoding', required=True, default='any', selection=[
            ('any', 'Any'),
            ('ean13', 'EAN-13'),
            ('ean8', 'EAN-8'),
            ('upca', 'UPC-A'),
        ], help='This rule will apply only if the barcode is encoded with the specified encoding')
    type = fields.Selection(
        string='Type', required=True, selection=[
            ('alias', 'Alias'),
            ('measure', 'Measure'),
            ('product', 'Unit Product'),
        ], default='product')
    pattern = fields.Char(string='Barcode Pattern', help="The barcode matching pattern", compute='_compute_pattern')
    alias = fields.Char(string='Alias', default='', help='The matched pattern will alias to this barcode')
    rule_part_ids = fields.One2many('barcode.rule.part', 'rule_id')
    is_combined = fields.Boolean(related="barcode_nomenclature_id.is_combined")
    required_rule_ids = fields.Many2many(
        'barcode.rule', 'barcode_rule_required_rel', 'required_rule_ids', 'child_rule_ids',
        string="Required Rule",
        help="When set, this rule can be used only when at least one of the required "
             "rule is also present in the parsed barcode.")
    child_rule_ids = fields.Many2many(
        'barcode.rule', 'barcode_rule_required_rel', 'child_rule_ids', 'required_rule_ids',
        string="Depending rules")
    associated_uom_id = fields.Many2one(related='rule_part_ids.associated_uom_id')

    @api.depends('rule_part_ids', 'rule_part_ids.sequence')
    def _compute_pattern(self):
        for rule in self:
            if not rule.rule_part_ids:
                rule.pattern = ''
                continue
            patterns = rule.rule_part_ids.sorted('sequence').mapped('pattern')
            rule.pattern = ''.join(patterns)


class BarcodeRulePart(models.Model):
    _name = 'barcode.rule.part'
    _description = 'Barcode Rule - Catching Group'
    _order = 'sequence asc, id'

    sequence = fields.Integer(string='Order', help="Must follow the rule pattern groups order")
    type = fields.Selection(
        string='Type', required=True, selection=[
            ('alias', 'Alias'),
            ('prefix', 'Prefix'),  # TODO: Maybe useless, to remove ?
            ('product', 'Unit Product'),
            ('measure', 'Measure'),
            ('decimal_position', 'Decimal Position'),
        ], default='product')
    rule_id = fields.Many2one('barcode.rule')
    encoding = fields.Selection(
        string='Encoding', required=True, default='any', selection=[
            ('any', 'Any'),
            ('ean13', 'EAN-13'),
            ('ean8', 'EAN-8'),
            ('upca', 'UPC-A'),
        ], help="This barcode part catched by the rule's pattern have to use the set encoding, "
                "which usually include the use of a checksume digit")
    pattern = fields.Char(string='Group Pattern', required=True, default='')
    associated_uom_id = fields.Many2one('uom.uom')
    decimal_position = fields.Integer("Decimal Position")
    hide_decimal_position = fields.Boolean(compute='_compute_hide_decimal_position')

    @api.depends('rule_id.rule_part_ids', 'type')
    def _compute_hide_decimal_position(self):
        self.hide_decimal_position = True
        for rule_group in self:
            if rule_group.type == 'measure':
                # The decimal position field should not be visible if it's defined on another group.
                rule_groups = rule_group.rule_id.rule_part_ids
                rule_group.hide_decimal_position = 'decimal_position' in rule_groups.mapped('type')

    @api.depends('type')
    def _compute_name(self):
        for rule_group in self:
            rule_group.display_name = rule_group.type

    @api.constrains('pattern')
    def _check_pattern(self):
        for rule_group in self:
            try:
                # Rule group patterns use regex, checks the regex is valid.
                compiled_regex = re.compile(rule_group.pattern)
                # Check the rule group's pattern has only one catching groups.
                if compiled_regex.groups != 1:
                    raise ValidationError(_(
                        "The pattern \"%s\" is not valid, it should have one catching group.",
                        rule_group.pattern))
            except re.error as error:
                raise ValidationError(
                    _("The pattern \"%s\" is not a valid Regex: ", rule_group.pattern) + str(error))
            continue

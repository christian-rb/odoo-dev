# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.fields import Command

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.uom.tests.common import UomCommon


class ProductCommon(
    BaseCommon,  # enforce constant test currency (USD)
    UomCommon,
):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.env.company.currency_id = cls.env.ref('base.USD')
        cls.currency = cls.env.ref('base.USD')

        # Ideally, this logic should be moved into sthg like a NoAccountCommon in account :D
        # Since tax fields are specified in account module, cannot be given as create values
        NO_TAXES_CONTEXT = {
            'default_taxes_id': False
        }

        cls.product_category = cls.env['product.category'].create({
            'name': 'Test Category',
        })
        cls.product = cls.env['product.product'].with_context(**NO_TAXES_CONTEXT).create({
            'name': 'Test Product',
            'detailed_type': 'consu',
            'list_price': 20.0,
            'categ_id': cls.product_category.id,
        })
        cls.service_product = cls.env['product.product'].with_context(**NO_TAXES_CONTEXT).create({
            'name': 'Test Service Product',
            'detailed_type': 'service',
            'list_price': 50.0,
            'categ_id': cls.product_category.id,
        })
        cls.consumable_product = cls.product
        cls.pricelist = cls.env['product.pricelist'].create({
            'name': 'Test Pricelist',
        })
        cls._archive_other_pricelists()

    @classmethod
    def _archive_other_pricelists(cls):
        cls.env['product.pricelist'].search([
            ('id', '!=', cls.pricelist.id),
        ]).action_archive()


class ProductAttributesCommon(ProductCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.size_attribute = cls.env['product.attribute'].create({
            'name': 'Size',
            'value_ids': [
                Command.create({'name': 'S'}),
                Command.create({'name': 'M'}),
                Command.create({'name': 'L'}),
            ]
        })
        (
            cls.size_attribute_s,
            cls.size_attribute_m,
            cls.size_attribute_l,
        ) = cls.size_attribute.value_ids

        cls.color_attribute = cls.env['product.attribute'].create({
            'name': 'Color',
            'value_ids': [
                Command.create({'name': 'red', 'sequence': 1}),
                Command.create({'name': 'blue', 'sequence': 2}),
                Command.create({'name': 'green', 'sequence': 3}),
            ],
        })
        (
            cls.color_attribute_red,
            cls.color_attribute_blue,
            cls.color_attribute_green,
        ) = cls.color_attribute.value_ids

        cls.no_variant_attribute = cls.env['product.attribute'].create({
            'name': 'No variant',
            'create_variant': 'no_variant',
            'value_ids': [
                Command.create({'name': 'extra'}),
                Command.create({'name': 'second'}),
            ]
        })
        (
            cls.no_variant_attribute_extra,
            cls.no_variant_attribute_second,
        ) = cls.no_variant_attribute.value_ids


class ProductVariantsCommon(ProductAttributesCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.product_template_sofa = cls.env['product.template'].create({
            'name': 'Sofa',
            'uom_id': cls.uom_unit.id,
            'uom_po_id': cls.uom_unit.id,
            'categ_id': cls.product_category.id,
            'attribute_line_ids': [Command.create({
                'attribute_id': cls.color_attribute.id,
                'value_ids': [Command.set([
                    cls.color_attribute_red.id,
                    cls.color_attribute_blue.id,
                    cls.color_attribute_green.id
                ])],
            })]
        })

        cls.product_template_shirt = cls.env['product.template'].create({
            'name': 'Shirt',
            'categ_id': cls.product_category.id,
            'attribute_line_ids': [
                Command.create({
                    'attribute_id': cls.size_attribute.id,
                    'value_ids': [Command.set([cls.size_attribute_l.id])],
                }),
            ],
        })


class TestProductCommon(ProductVariantsCommon):
    pass

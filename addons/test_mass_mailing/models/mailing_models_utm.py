# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class UtmTestSourceMixin(models.Model):
    """ Test utm.source.mixin """
    _description = "UTM Source Mixin Test Model"
    _name = "utm.test.source.mixin"
    _order = "id DESC"
    _rec_name = "title"
    _inherit = [
        "utm.source.mixin",
    ]

    name = fields.Char(inherited=True)
    title = fields.Char()


class UtmTestSourceMixinImp(models.Model):
    """ Test utm.source.mixin, with additional fields, allowing also to test
    cross model uniqueness check """
    _description = "Improved UTM Source Mixin Test Model"
    _name = "utm.test.source.mixin.imp"
    _order = "id DESC"
    _rec_name = "title"
    _inherit = [
        "mail.thread",
        "utm.source.mixin",
    ]

    name = fields.Char(inherited=True)
    title = fields.Char()

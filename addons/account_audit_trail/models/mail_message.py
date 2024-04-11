# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from markupsafe import Markup

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Message(models.Model):
    _inherit = 'mail.message'

    account_audit_log_preview = fields.Html(string="Description", compute="_compute_account_audit_log_preview")
    account_audit_log_activated = fields.Boolean(
        string="Audit Log Activated",
        compute="_compute_account_audit_log_activated",
        search="_search_account_audit_log_activated")

    def _compute_account_audit_log_preview(self):
        for message in self:
            title = message.subject or message.preview
            tracking_value_ids = message.sudo().tracking_value_ids._filter_has_field_access(self.env)
            if not title and tracking_value_ids:
                title = _("Updated")
            elif not title and message.subtype_id and not message.subtype_id.internal:
                title = message.subtype_id.display_name
            audit_log_preview = Markup("<div>%s</div>") % title
            for fmt_vals in tracking_value_ids._tracking_value_format():
                field_desc = fmt_vals['changedField']
                old_value = fmt_vals['oldValue']['value']
                new_value = fmt_vals['newValue']['value']
                audit_log_preview += Markup(
                    "<li>%(old_value)s <i class='o_TrackingValue_separator fa fa-long-arrow-right mx-1 text-600' title='%(title)s' role='img' aria-label='%(title)s'></i>%(new_value)s (%(field)s)</li>"
                ) % {
                    'old_value': old_value,
                    'new_value': new_value,
                    'title': _("Changed"),
                    'field': field_desc,
                }
            message.account_audit_log_preview = audit_log_preview

    @api.depends('model', 'res_id')
    def _compute_account_audit_log_activated(self):
        move_messages = self.filtered(lambda m: m.model == 'account.move' and m.res_id)
        (self - move_messages).account_audit_log_activated = False
        if move_messages:
            moves = self.env['account.move'].sudo().search([
                ('id', 'in', move_messages.mapped('res_id')),
                ('company_id.check_account_audit_trail', '=', True),
            ])
            for message in move_messages:
                message.account_audit_log_activated = message.res_id in moves.ids

    def _search_account_audit_log_activated(self, operator, value):
        if operator not in ['=', '!='] or not isinstance(value, bool):
            raise UserError(_('Operation not supported'))
        move_query = self.env['account.move']._search([('company_id.check_account_audit_trail', operator, value)])
        return ['&', ('model', '=', 'account.move'), ('res_id', 'in', move_query)]

# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class ResUsersSettings(models.Model):
    _inherit = "res.users.settings"

    # Calendar module settings.
    calendar_default_privacy = fields.Selection(
        [('public', 'Public'),
         ('private', 'Private'),
         ('confidential', 'Only internal users')],
        'Calendar Default Privacy', default='public', required=True,
        store=True, readonly=False, help="Default privacy setting for whom the calendar events will be visible."
    )

    # Calendar filters to shown/hide calendar events in the calendar view.
    show_own_calendar_filter = fields.Boolean(
        string="Show own calendar", default=True, groups="base.group_system",
        help="Show own calendar events in the calendar view."
    )
    show_all_calendars_filter = fields.Boolean(
        string="Show everybody's calendar", default=False, groups="base.group_system",
        help="Show everybody's calendar in the calendar view."
    )

    @api.model
    def _get_fields_blacklist(self):
        """ Get list of calendar fields that won't be formatted in session_info. """
        calendar_fields_blacklist = ['calendar_default_privacy', 'show_all_calendars_filter', 'show_own_calendar_filter']
        return super()._get_fields_blacklist() + calendar_fields_blacklist

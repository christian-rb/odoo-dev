# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResUsersSettings(models.Model):
    _inherit = "res.users.settings"

    # Microsoft Calendar settings.
    microsoft_calendar_sync_token = fields.Char('Microsoft Next Sync Token', copy=False, groups='base.group_system')
    microsoft_synchronization_stopped = fields.Boolean('Outlook Synchronization stopped', copy=False, groups='base.group_system')
    microsoft_last_sync_date = fields.Datetime('Last Sync Date', copy=False, help='Last synchronization date with Outlook Calendar', groups='base.group_system')
    microsoft_sync_status = fields.Selection([
        ('sync_active', 'Active'),
        ('sync_paused', 'Paused'),
        ('sync_stopped', 'Stopped'),
        ('missing_credentials', 'Missing Credentials'),
        ], string='Outlook Sync Status', readonly=True, store=False, compute='_compute_microsoft_sync_status')

    @api.model
    def _get_fields_blacklist(self):
        """ Get list of microsoft fields that won't be formatted in session_info. """
        microsoft_fields_blacklist = [
            'microsoft_calendar_sync_token',
            'microsoft_synchronization_stopped',
            'microsoft_last_sync_date',
            'microsoft_sync_status'
        ]
        return super()._get_fields_blacklist() + microsoft_fields_blacklist

    def _compute_microsoft_sync_status(self):
        """ Compute the Outlook Calendar synchronization's status. """
        for setting in self:
            setting.microsoft_sync_status = setting.user_id.check_synchronization_status().get('microsoft_calendar')

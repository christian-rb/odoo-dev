# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models
# from odoo.tools import str2bool

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    cal_client_id = fields.Char("Client_id", config_parameter='google_calendar_client_id', default='')
    cal_client_secret = fields.Char("Client_key", config_parameter='google_calendar_client_secret', default='')
    cal_sync_paused = fields.Boolean("Google Synchronization Paused", config_parameter='google_calendar_sync_paused',
        help="Indicates if synchronization with Google Calendar is paused or not.")

    # def get_values(self):
    #     res = super().get_values()
    #     calendar_paused = str2bool(self.env['ir.config_parameter'].sudo().get_param('google_calendar_sync_paused'))
    #     if not calendar_paused and self.env.user.google_calendar_account_id and \
    #             self.env.user.google_calendar_account_id._google_calendar_authenticated() and \
    #             self.env.user.check_calendar_credentials().get('google_calendar', False):
    #         self.env['calendar.recurrence']._restart_google_sync()
    #         self.env['calendar.event']._restart_google_sync()
    #     return res

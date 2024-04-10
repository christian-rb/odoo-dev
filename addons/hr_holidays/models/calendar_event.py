from odoo import models


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    def _need_video_call(self):
        for record in self:
            return record.res_model != 'hr.leave'

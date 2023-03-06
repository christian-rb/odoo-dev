from odoo import api, models

class CalendarEventMandatoryDay(models.Model):
    _inherit = "calendar.event"

    @api.model
    def get_unusual_days(self, date_from, date_to=None):
        return self.env.user.employee_id._get_unusual_days(date_from, date_to)

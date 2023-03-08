# Part of Odoo. See LICENSE file for full copyright and licensing details.

from pytz import timezone
from datetime import datetime, time
from dateutil.relativedelta import relativedelta

from odoo import models


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    def _get_calendar(self, start=None, stop=None):
        self.ensure_one()
        if not start:
            return False
        if not stop:
            stop = start
        return self.sudo()._get_contracts(
            start.replace(hour=0, minute=0, second=0),
            stop.replace(hour=23, minute=59, second=59),
            states=['open', 'close']).resource_calendar_id

    def _get_calendar_periods(self, start, stop):
        self.ensure_one()
        contracts = self.sudo()._get_contracts(
            start.replace(hour=0, minute=0, second=0),
            stop.replace(hour=23, minute=59, second=59),
            states=['open', 'close'])

        result = []
        for contract in contracts:
            date_start = datetime.combine(contract.date_start, time(0, 0, 0)).replace(tzinfo=timezone(contract.resource_calendar_id.tz)).astimezone(timezone('UTC'))
            if contract.date_end:
                date_end = datetime.combine(contract.date_end + relativedelta(days=1), time(0, 0, 0)).replace(tzinfo=timezone(contract.resource_calendar_id.tz)).astimezone(timezone('UTC'))
            else:
                date_end = stop
            result.append((max(date_start, start), min(date_end, stop), contract.resource_calendar_id))

        return result

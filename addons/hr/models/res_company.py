# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class Company(models.Model):
    _inherit = 'res.company'

    hr_presence_control_email_amount = fields.Integer(string="# emails to send")
    hr_presence_control_ip_list = fields.Char(string="Valid IP addresses")
    employee_properties_definition = fields.PropertiesDefinition('Employee Properties')
    hr_presence_control = fields.Selection([
        ('user_status', 'User connection status'),
        ('user_email', 'Amount of emails sent'),
        ('user_ip', 'IP Address')],
        string="Presence Control",
        default='user_status',
    )

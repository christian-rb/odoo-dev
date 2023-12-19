
from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    resource_calendar_id = fields.Many2one(
        'resource.calendar', 'Company Working Hours',
        related='company_id.resource_calendar_id', readonly=False)
    module_hr_skills = fields.Boolean(string="Skills Management")
    module_hr_homeworking = fields.Boolean(string="Remote Work")
    hr_presence_control = fields.Selection(related="company_id.hr_presence_control", readonly=False)
    hr_presence_control_email_amount = fields.Integer(related="company_id.hr_presence_control_email_amount", readonly=False)
    hr_presence_control_ip_list = fields.Char(related="company_id.hr_presence_control_ip_list", readonly=False)
    hr_employee_self_edit = fields.Boolean(string="Employee Editing", config_parameter='hr.hr_employee_self_edit')


    @api.model_create_multi
    def create(self, vals_list):
        configs = super().create(vals_list)
        hr_presence_module = self.env['ir.module.module'].sudo().search([('name', '=', 'hr_presence'), ('state', '=', 'uninstalled')])
        if hr_presence_module and any(config.hr_presence_control in ['user_ip', 'user_email'] for config in configs):
            hr_presence_module.button_immediate_install()
        return configs

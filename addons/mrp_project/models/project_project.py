#  Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class Project(models.Model):
    _inherit = "project.project"

    production_ids = fields.One2many('mrp.production', 'project_id', groups='mrp.group_mrp_user')
    production_count_direct_link = fields.Integer(compute='_compute_production_count')

    def _compute_production_count(self):
        for record in self:
            record.production_count_direct_link = len(record.production_ids)

    def action_view_linked_mrp_productions(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('mrp.mrp_production_action')
        action['domain'] = [('id', 'in', self.production_ids.ids)]
        if self.production_count == 1:
            action['view_mode'] = 'form'
            action['res_id'] = self.production_ids.id
            if 'views' in action:
                action['views'] = [
                    (view_id, view_type)
                    for view_id, view_type in action['views']
                    if view_type == 'form'
                ] or [False, 'form']
        return action

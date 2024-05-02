#  Part of Odoo. See LICENSE file for full copyright and licensing details.
import ast
from odoo import fields, models, _
from odoo.osv.expression import AND


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    project_id = fields.Many2one('project.project', groups='project.group_project_user')
    task_count = fields.Integer(compute='_compute_tasks_count')

    def _compute_tasks_count(self):
        for production in self:
            production.task_count = production.project_id.task_count if production.project_id else 0

    def action_view_linked_project(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Project'),
            'res_id': self.project_id.id,
            'res_model': 'project.project',
            'views': [(False, 'form')],
            'view_mode': 'kanban,tree,form'
        }
        return action

    def action_view_tasks(self):
        self.ensure_one()

        list_view_id = self.env.ref('project.view_task_tree2').id
        form_view_id = self.env.ref('project.view_task_form2').id
        kanban_view_id = self.env.ref('project.view_task_kanban_inherit_view_default_project').id

        action = self.env["ir.actions.actions"]._for_xml_id("project.action_view_task")
        action['views'] = [[kanban_view_id, 'kanban'], [list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'calendar'], [False, 'pivot']]

        action['context'] = {
            'default_project_id': self.project_id.id,
            'default_user_ids': [self.env.uid],
        }
        action['domain'] = AND([ast.literal_eval(action['domain']), [('id', 'in', self.project_id.task_ids.ids)]])
        return action

    def action_create_project(self):
        self.ensure_one()
        values = {
            'name': self.name,
            'active': True,
            'company_id': self.company_id.id,
            'user_id': False,
        }
        if len(self.analytic_account_ids) == 1:
            values['analytic_account_id'] = self.analytic_account_ids.id

        # The no_create_folder context key is used in documents_project
        project = self.env['project.project'].with_context(no_create_folder=True).create(values)

        # Avoid new tasks to go to 'Undefined Stage'
        if not project.type_ids:
            project.type_ids = self.env['project.task.type'].create([{
                'name': name,
                'fold': fold,
                'sequence': sequence,
            } for name, fold, sequence in [
                (_('To Do'), False, 5),
                (_('In Progress'), False, 10),
                (_('Done'), False, 15),
                (_('Cancelled'), True, 20),
            ]])

        self.project_id = project
        return self.action_view_linked_project()

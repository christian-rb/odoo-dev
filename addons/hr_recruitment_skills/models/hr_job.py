from markupsafe import Markup
from ast import literal_eval
from odoo import fields, models, _

class HrJob(models.Model):
    _inherit = "hr.job"

    skill_ids = fields.Many2many('hr.skill', string="Expected Skills")

    def action_search_matching_applicant(self):
        action = self.env['ir.actions.actions']._for_xml_id('hr_recruitment.crm_case_categ0_act_job')
        action['name'] = _("Matching Applicants")
        action['views'] = [(self.env.ref('hr_recruitment_skills.crm_case_tree_view_inherit_hr_recruitment_skills').id, 'tree'), (False, 'form')]
        action['context'] = literal_eval(action.get('context'))
        action['context'].update({'active_id': self.id})
        action['domain'] = [
            ('job_id', '!=', self.id),
            ('skill_ids', 'in', self.skill_ids.ids)
        ]
        action['help'] = Markup('<p class="o_view_nocontent_empty_folder">No Matching Applicants</p>\
            <p>We do not have any applicants who meet the skill requirements for this job position in the database at the moment.</p>')
        return action

# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProjectSharingCollaboratorWizard(models.TransientModel):
    _name = 'project.share.collaborator.wizard'
    _description = 'Project Sharing Collaborator Wizard'

    parent_wizard_id = fields.Many2one('project.share.wizard', string='Project Share Wizard', export_string_translation=False)
    partner_id = fields.Many2one('res.partner', string='Collaborator', required=True)
    access_mode = fields.Selection([('read', 'Read-only'), ('edit', 'Edit'), ('edit_limited', 'Edit with limited access')], required=True)

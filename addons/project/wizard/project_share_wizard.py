# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import Command, api, fields, models, _


class ProjectShareWizard(models.TransientModel):
    _name = 'project.share.wizard'
    _inherit = 'portal.share'
    _description = 'Project Sharing'

    @api.model
    def default_get(self, fields):
        # The project share action could be called in `project.collaborator`
        # and so we have to check the active_model and active_id to use
        # the right project.
        active_model = self._context.get('active_model', '')
        active_id = self._context.get('active_id', False)
        if active_model == 'project.collaborator':
            active_model = 'project.project'
            active_id = self._context.get('default_project_id', False)
        result = super(ProjectShareWizard, self.with_context(active_model=active_model, active_id=active_id)).default_get(fields)
        if not result.get('access_mode'):
            result['access_mode'] = 'read'
        if result['res_model'] and result['res_id']:
            project = self.env[result['res_model']].browse(result['res_id'])
            collaborator_vals_list = []
            collaborator_ids = []
            for collaborator in project.collaborator_ids:
                collaborator_ids.append(collaborator.partner_id.id)
                collaborator_vals_list.append(Command.create({
                    'partner_id': collaborator.partner_id.id,
                    'access_mode': 'edit',
                }))
            for follower in project.message_partner_ids:
                if follower.partner_share and follower.id not in collaborator_ids:
                    collaborator_vals_list.append(Command.create({
                        'partner_id': follower.id,
                        'access_mode': 'read',
                    }))
            if collaborator_vals_list:
                result['collaborator_ids'] = collaborator_vals_list
            else:
                result['hide_collaborator'] = True
        return result

    @api.model
    def _selection_target_model(self):
        project_model = self.env['ir.model']._get('project.project')
        return [(project_model.model, project_model.name)]

    access_mode = fields.Selection([('read', 'Read-only'), ('edit', 'Edit')])
    send_email = fields.Boolean(string="Send by Email")
    collaborator_ids = fields.One2many('project.share.collaborator.wizard', 'parent_wizard_id', string='Collaborators')
    hide_collaborator = fields.Boolean(export_string_translation=False, store=False, readonly=True)

    @api.depends('res_model', 'res_id')
    def _compute_resource_ref(self):
        for wizard in self:
            if wizard.res_model and wizard.res_model == 'project.project':
                wizard.resource_ref = '%s,%s' % (wizard.res_model, wizard.res_id or 0)
            else:
                wizard.resource_ref = None

    @api.model_create_multi
    def create(self, vals_list):
        wizards = super().create(vals_list)
        for wizard in wizards:
            collaborator_ids_to_add = []
            collaborator_ids_to_remove = []
            project = wizard.resource_ref
            for collaborator in wizard.collaborator_ids:
                if collaborator.access_mode == "edit" and collaborator.partner_id not in project.collaborator_ids.partner_id:
                    collaborator_ids_to_add.append(collaborator.partner_id.id)
                elif collaborator.access_mode == "read" and collaborator.partner_id in project.collaborator_ids.partner_id:
                    collaborator_ids_to_remove.append(collaborator.partner_id.id)
            if collaborator_ids_to_add:
                project._add_collaborators(self.env['res.partner'].browse(collaborator_ids_to_add))
            collaborator_ids_to_remove += project.collaborator_ids.partner_id.filtered(lambda p: p not in wizard.collaborator_ids.partner_id).ids
            project.message_partner_ids = project.message_partner_ids.filtered(lambda p: not p.partner_share or p in wizard.collaborator_ids.partner_id)
            if collaborator_ids_to_remove:
                project.collaborator_ids.filtered(lambda c: c.partner_id.id in collaborator_ids_to_remove).unlink()
        return wizards

    def action_share_record(self):
        # Confirmation dialog is only opened if new portal user(s) need to be created in a 'on invitation' website
        self.ensure_one()
        on_invite = self.env['res.users']._get_signup_invitation_scope() == 'b2b'
        new_portal_user = self.partner_ids.filtered(lambda p: not p.user_ids) and on_invite
        if not new_portal_user:
            return self.action_send_mail()
        return {
            'name': _('Confirmation'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'views': [(self.env.ref('project.project_share_wizard_confirm_form').id, 'form')],
            'res_model': 'project.share.wizard',
            'res_id': self.id,
            'target': 'new',
            'context': self.env.context,
        }

    def action_send_mail(self):
        self.env['project.project'].browse(self.res_id).privacy_visibility = 'portal'
        if self.access_mode == 'edit' or self.send_email:
            portal_partners = self.partner_ids.filtered('user_ids')
            if self.access_mode == 'edit':
                self.resource_ref._add_collaborators(self.partner_ids)
            # send mail to users
            self._send_public_link(portal_partners)
            self._send_signup_link(partners=self.with_context({'signup_valid': True}).partner_ids - portal_partners)
            self.resource_ref._add_followers(self.partner_ids)
            return {'type': 'ir.actions.act_window_close'}
        return super().action_send_mail()

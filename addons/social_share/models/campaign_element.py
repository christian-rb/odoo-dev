import base64

from odoo import _, api, exceptions, fields, models

class CampaignElement(models.Model):
    _name = 'snshare.campaign.element'
    _description = 'Social Share Campaign Element'
    _sql_constraints = [('role_uniq', "unique(campaign_id, role)", "Each campaign should only have one element for each role.")]

    model = fields.Selection(related='campaign_id.model')
    campaign_id = fields.Many2one('snshare.campaign', ondelete='cascade')

    role = fields.Selection([
        ('background', 'Background'),
        ('header', 'Header'),
        ('subheader', 'Sub-Header'),
        ('section_1', 'Section 1'),
        ('subsection_1', 'Sub-Section 1'),
        ('subsection_2', 'Sub-Section 2'),
        ('button', 'Button'),
        ('image_1', 'Image 1'),
        ('image_2', 'Image 2')
    ], required=True)

    render_type = fields.Selection([('image', 'Image'), ('text', 'User Text')], default='text', required=True, ondelete={'image': 'cascade', 'text': 'cascade'})
    value_type = fields.Selection([('static', 'Manual'), ('field', 'Dynamic')], default='static', required=True)

    # image shape
    image = fields.Image(attachment=False)
    # text user input
    text = fields.Text()
    text_color = fields.Char(default="ffffff")
    # text field
    field_path = fields.Char()

    @api.constrains('field_path', 'model')
    def _check_fields(self):
        skip_security = self.env.su or self.env.user._is_admin()
        for element in self.filtered(lambda e: e.value_type == 'field'):
            # check we can start from this model
            Model = self.env[element.model]
            if not skip_security and not Model._snshare_allowed_model():
                raise exceptions.ValidationError(_('%(model_name)s cannot be used for share campaigns.', model_name=Model._name))
            # check all of the fields are allowed
            for field_name in element.field_path.split('.'):
                if not skip_security and field_name not in Model._snshare_allowed_fields():
                    raise exceptions.ValidationError(_('%(model_name)s.%(field_name)s cannot be used for share campaigns.', model_name=Model._name, field_name=field_name))
                LastModel = Model
                Model = Model[field_name]
            # check the last field has a sensible type
            if isinstance(Model, models.Model):
                raise exceptions.ValidationError(_('Path for share campaign dynamic value should not lead to a value, not a record of type %(model_name)s.', model_name=Model._name))
            if element.render_type == 'image' and LastModel._fields[field_name].type != 'binary':
                raise exceptions.ValidationError(_('%(model_name)s.%(field_name)s cannot be used as an image value for %(element_role)s', model_name=LastModel._name, field_name=field_name, element_role=element.role))

    def _get_value(self, record=None):
        if self.value_type == 'field':
            if not record:
                if self.render_type == 'image':
                    return base64.b64encode(self.env['ir.binary']._placeholder())
                return None
            values = record.mapped(self.field_path)  # use map to automatically follow relations
            return values[0] if values else None
        if self.render_type == 'image':
            return self.image
        if self.render_type == 'text':
            return self.text

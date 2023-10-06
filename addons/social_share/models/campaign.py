from lxml import html
import base64
from markupsafe import Markup

from odoo import _, api, Command, fields, models
from ..controllers.main import SocialShareController
from ..utils.image_utils import scale_image_b64
from .template import TEMPLATE_DIMENSIONS

class Campaign(models.Model):
    _name = 'snshare.campaign'
    _description = 'Social Share Campaign'
    _inherit = ['mail.activity.mixin', 'mail.thread', 'utm.source.mixin']

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    model_id = fields.Many2one('ir.model', compute='_compute_model_id', store=True)
    model = fields.Selection(string="Model Name", selection=[('res.partner', 'Contact')], default="res.partner")
    template_group_id = fields.Many2one(
        'snshare.template.group',
        string="Layout",
        domain="['|', ('model_id', '=', False), ('model_id', '=', model_id)]",
    )
    template_id = fields.Many2one(
        'snshare.template',
        string="Design",
        domain="[('template_group_id', '=?', template_group_id)]",
    )

    post_suggestion = fields.Text()
    tag_ids = fields.Many2many('snshare.campaign.tag', string='Tags')
    target_url = fields.Char(string='Shared Link', required=True)
    target_url_redirected = fields.Char(compute='_compute_target_url_redirected')
    thanks_message = fields.Html(string='Thank-You Message')
    thanks_redirection = fields.Char(string='Redirect Address')
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user, domain="[('share', '=', False)]")

    element_ids = fields.One2many('snshare.campaign.element', inverse_name='campaign_id')

    image = fields.Image(compute='_compute_image', store=True)
    link_tracker_id = fields.Many2one('link.tracker', ondelete="restrict")

    target_url_click_count = fields.Integer(compute='_compute_target_url_click_count')
    share_url_ids = fields.One2many('snshare.url', inverse_name='campaign_id')
    share_url_click_count = fields.Integer(compute='_compute_share_url_click_count')
    share_url_share_count = fields.Integer(compute='_compute_share_url_share_count')

    mail_template_id = fields.Many2one('mail.template')
    def default_get(self, vals):
        default_vals = super().default_get(vals)
        if 'element_ids' in vals:
            default_vals['element_ids'] = [
                Command.create({'role': 'background', 'render_type': 'image'}),
                Command.create({'role': 'header', 'render_type': 'text'}),
                Command.create({'role': 'subheader', 'render_type': 'text'}),
                Command.create({'role': 'section_1', 'render_type': 'text'}),
                Command.create({'role': 'subsection_1', 'render_type': 'text'}),
                Command.create({'role': 'subsection_2', 'render_type': 'text'}),
                Command.create({'role': 'button', 'render_type': 'text'}),
                Command.create({'role': 'image_1', 'render_type': 'image'}),
                Command.create({'role': 'image_2', 'render_type': 'image'}),
            ]
        return default_vals

    @api.model_create_multi
    def create(self, create_vals):
        campaign_ids = super().create(create_vals)
        link_tracker_ids = self.env['link.tracker'].create([
            {
                'url': campaign.target_url,
                'title': campaign.name,  # not having this will trigger a request in the create
                'source_id': campaign.source_id.id,
            } for campaign in campaign_ids
        ])

        mail_template_ids = self.env['mail.template'].create([{
            'name': f'snshare {campaign.name} template',
            'model_id': campaign.model_id.id if campaign.model_id else False,
            'body_html': Markup(
                '<div id="message"></div>'
                f"""<a t-att-href="object.env['snshare.campaign'].browse({campaign.id})._get_url(object.id)" class="o_no_link_popover">{_("Your Card")}</a>"""
            ),
        } for campaign in campaign_ids])

        for campaign, tracker, template in zip(campaign_ids, link_tracker_ids, mail_template_ids):
            campaign.write({'link_tracker_id': tracker.id, 'mail_template_id': template.id})
        return campaign_ids

    def unlink(self):
        self.mail_template_id.unlink()
        return super().unlink()

    def write(self, vals):
        write_ret = super().write(vals)
        for campaign in self:
            link_tracker_vals = {}
            if 'source_id' in vals:
                link_tracker_vals['source_id'] = campaign.source_id
            if 'target_url' in vals:
                link_tracker_vals['url'] = campaign.target_url
            if 'model_id' in vals:
                campaign.mail_template_id.model_id = campaign.model_id
            if link_tracker_vals.keys():
                campaign.link_tracker_id.write(link_tracker_vals)
        return write_ret

    @api.depends('link_tracker_id.count')
    def _compute_target_url_click_count(self):
        for campaign in self:
            campaign.target_url_click_count = self.link_tracker_id.count

    @api.depends('share_url_ids.visited')
    def _compute_share_url_click_count(self):
        for campaign in self:
            campaign.share_url_click_count = len(campaign.share_url_ids.filtered('visited'))

    @api.depends('share_url_ids.shared')
    def _compute_share_url_share_count(self):
        for campaign in self:
            campaign.share_url_share_count = len(campaign.share_url_ids.filtered('shared'))

    @api.depends('link_tracker_id.short_url')
    def _compute_target_url_redirected(self):
        for campaign in self:
            campaign.target_url_redirected = campaign.link_tracker_id.short_url or campaign.target_url

    @api.depends('model')
    def _compute_model_id(self):
        model_from_name = self.env['ir.model'].search([('model', 'in', self.mapped('model'))]).grouped('model')
        for campaign in self:
            campaign.model_id = model_from_name.get(campaign.model, False)

    @api.depends('template_id.body', 'element_ids')
    def _compute_image(self):
        campaigns_with_template = self.filtered('template_id.body')
        for campaign, image in zip(campaigns_with_template, campaigns_with_template._get_images_b64(with_demo_values=True)):
            campaign.image = scale_image_b64(image, 0.5)

    def _get_bodies(self, record=None, with_demo_values=False):
        demo_values = {} if not with_demo_values else {
            'header': _('Title'),
            'subheader': _('Subtitle'),
        }
        return [
            self.env['ir.qweb']._render(
                html.fromstring(campaign.template_id.body),
                {
                    element.role: element._get_value(record=record) or demo_values.get(element.role)
                    for element in campaign.element_ids
                } | {
                    f'{element.role}_color': element.text_color
                    for element in campaign.element_ids
                },
                raise_on_code=False,
            ) if campaign.template_id.body else '' for campaign in self
        ]

    def _get_images_bytes(self, record=None, with_demo_values=False):
        bodies = self._get_bodies(record=record, with_demo_values=with_demo_values)
        if self and bodies:
            return self.env['ir.actions.report']._run_wkhtmltoimage(
                bodies,
                *TEMPLATE_DIMENSIONS
            )
        return [b''] * len(self)

    def _get_images_b64(self, record=None, with_demo_values=False):
        return [
            base64.b64encode(image_bytes) for image_bytes
            in self._get_images_bytes(record=record, with_demo_values=with_demo_values)
        ]

    @api.onchange('template_group_id')
    def _onchange_template_group_id(self):
        for campaign in self:
            campaign.template_id = campaign.template_group_id.template_ids[:1]

    def action_open_url_share(self):
        """Open url dialog."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Share Link'),
            'res_model': 'snshare.url.share',
            'views': [[False, 'form']],
            'context': {
                'default_campaign_id': self.id,
                'dialog_size': 'medium',
            },
            'target': 'new',
        }

    def action_show_clicked_urls(self):
        self.ensure_one()
        return self.env["ir.actions.actions"]._for_xml_id("social_share.action_snshare_url") | {
            'context': {'search_default_filter_visited': True},
            'domain': [('campaign_id', '=', self.id)],
        }

    def action_show_shared_urls(self):
        self.ensure_one()
        return self.env["ir.actions.actions"]._for_xml_id("social_share.action_snshare_url") | {
            'context': {'search_default_filter_shared': True},
            'domain': [('campaign_id', '=', self.id)],
        }

    def action_share_multi(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Send Share URLS'),
            'res_model': 'snshare.url.share.multi',
            'context': {'default_share_campaign_id': self.id, 'default_subject': self.name},
            'views': [[False, 'form']],
            'target': 'new',
        }

    def _get_url(self, record_id):
        self.ensure_one()
        uuid = False
        if self.model_id:
            existing_url = self.share_url_ids.filtered(lambda rec: rec.res_id == record_id)
            if existing_url:
                uuid = existing_url.uuid
            else:
                uuid = self.env['snshare.url'].create({'campaign_id': self.id, 'res_id': record_id}).uuid
        return SocialShareController._get_campaign_url(
            self, uuid
        )

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from ast import literal_eval
from odoo.osv import expression


class IrActionsTopbar(models.Model):
    _name = 'ir.actions.topbar'
    _description = 'Topbar Actions'
    _order = 'sequence, id'

    name = fields.Char(string='Topbar Name', translate=True)
    sequence = fields.Integer()
    parent_action_id = fields.Many2one('ir.actions.act_window', required=True, string='Parent Action', ondelete="cascade")
    parent_res_id = fields.Integer(string="Active Parent Id")
    parent_res_model = fields.Char(string='Active Parent Model', required=True)
    # It is required to have either action_id or python_action
    action_id = fields.Many2one('ir.actions.act_window', string="Action Id", ondelete="cascade")
    python_action = fields.Char(string="Python Action")

    user_id = fields.Many2one('res.users', string="Topbar user", help="User specific topbar action. If empty, shared topbar action", ondelete="cascade")
    is_deletable = fields.Boolean(compute="_compute_is_deletable")
    default_view_mode = fields.Char(string="Default view", help="Default view (if none, default view of the action is taken)")
    filter_ids = fields.One2many("ir.filters", "topbar_action_id", help="Default filter of the topbar action (if none, no filters)")
    is_visible = fields.Boolean(string="Topbar visibility", help="Computed field to check if the record should be visible according to the domain", compute="_compute_is_visible")
    domain = fields.Char(string='Domain Value', default="[]",
                         help="Domain applied to the active id of the parent model")
    context = fields.Char(string='Context Value', default="{}",
                          help="Context dictionary as Python expression, empty by default (Default: {})")
    groups_id = fields.Many2many('res.groups', 'ir_topbar_act_group_rel',
                                 'act_id', 'gid', string='Allowed Groups', help='Groups that can execute the topbar action. Leave empty to allow everybody.')

    _sql_constraints = [
        (
            'check_only_one_action_defined',
            """CHECK(
                (action_id IS NOT NULL AND python_action IS NULL) OR
                (action_id IS NULL AND python_action IS NOT NULL)
            )""",
            'Constraint to ensure that either an XML action or a Python action is defined, but not both.'
        ), (
            'check_python_action_requires_name',
            """CHECK(
                NOT (python_action IS NOT NULL AND name IS NULL)
            )""",
            'Constraint to ensure that if a Python action is defined, then the name must also be defined.'
        )
    ]

    @api.model_create_multi
    def create(self, vals_list):
        # The name by default is computed based on the triggered action if a action_id is defined.
        for vals in vals_list:
            if "name" not in vals:
                vals["name"] = _(self.env["ir.actions.act_window"].browse(vals["action_id"]).name)
        return super().create(vals_list)

    # The record is deletable if it hasn't been created from a xml record (i.e. is not a default topbar action)
    def _compute_is_deletable(self):
        external_ids = self._get_external_ids()
        for record in self:
            record_external_ids = external_ids[record.id]
            record.is_deletable = all(
                ex_id.startswith(("__export__", "__custom__")) for ex_id in record_external_ids
            )

    # Compute if the record should be visible to the user based on the domain applied to the active id of the parent
    # model and based on the groups allowed to access the record.
    def _compute_is_visible(self):
        active_id = self.env.context.get("active_id", False)
        if not active_id:
            for record in self:
                record.is_visible = False
            return
        domain_id = [("id", "=", active_id)]
        for record in self:
            action_groups = record.groups_id
            if not action_groups or (action_groups & self.env.user.groups_id):
                domain_model = literal_eval(record.domain)
                record.is_visible = self.env[record.parent_res_model].search_count(expression.AND([domain_id, domain_model]))
            else:
                record.is_visible = False

    # Delete the filters linked to a topbar action.
    @api.ondelete(at_uninstall=True)
    def _unlink_if_action_deletable(self):
        for record in self:
            if not record.is_deletable:
                raise UserError(_('You cannot delete a default topbar action'))

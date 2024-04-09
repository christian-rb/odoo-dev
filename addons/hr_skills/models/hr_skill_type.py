# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, Command


class SkillType(models.Model):
    _name = 'hr.skill.type'
    _description = "Skill Type"
    _order = "name"

    active = fields.Boolean('Active', default=True)
    name = fields.Char(required=True, translate=True)
    skill_ids = fields.One2many('hr.skill', 'skill_type_id', string="Skills")
    skill_level_ids = fields.One2many('hr.skill.level', 'skill_type_id', string="Levels")

    def copy(self, default=None):
        new_types = super().copy(default)
        for old_type, new_type in zip(self, new_types):
            new_skills_level = old_type.skill_level_ids.copy({"skill_type_id": new_type.id})
            new_type.write({
                'skill_level_ids': [(Command.set(new_skills_level.ids))]
                })
        return new_types

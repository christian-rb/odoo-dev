# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class EventRegistration(models.Model):
    _name = 'event.registration'
    _inherit = ['event.registration']

    visitor_id = fields.Many2one('website.visitor', string='Visitor', ondelete='set null')
    registration_answer_ids = fields.One2many('event.registration.answer', 'registration_id', string='Attendee Answers')
    registration_answer_choice_ids = fields.One2many('event.registration.answer', 'registration_id', string='Attendee Selection Answers',
        domain=[('question_type', '=', 'simple_choice')])

    def _get_website_registration_allowed_fields(self):
        return {'name', 'phone', 'email', 'company_name', 'event_id', 'partner_id', 'event_ticket_id'}

    def _get_registration_summary(self):
        res = super()._get_registration_summary()
        questions_answers = []
        for answer in self.registration_answer_ids:
            index = next((i for i, ans in enumerate(questions_answers) if ans['question'] == answer.question_id.title), None)
            answer_value = answer.value_answer_id.name if answer.question_type == 'simple_choice' else answer.value_text_box
            if index is not None:
                questions_answers[index]['answers'].append(answer_value)
            else:
                questions_answers.append({
                    'question': answer.question_id.title,
                    'answers': [answer_value],
                })
        res['registration_questions_answers'] = questions_answers
        return res

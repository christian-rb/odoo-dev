# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import Command
from odoo.addons.hr_expense.tests.common import TestExpenseCommon
from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user, tagged, users


@tagged('-at_install', 'post_install')
class TestExpensesAccessRights(TestExpenseCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        # Portal user & employee
        cls.expense_test_user_portal = new_test_user(cls.env, login='expense_test_user_portal', groups='base.group_portal')
        cls.expense_test_user_portal_employee = cls.env['hr.employee'].create({
            'name': 'expense_portal_employee',
            'user_id': cls.expense_test_user_portal.id,
            'address_home_id': cls.expense_test_user_portal.partner_id.id,
            'address_id': cls.expense_test_user_portal.partner_id.id,
        })

        # Base employee user & employee
        cls.expense_test_user_base_employee = new_test_user(cls.env, login='expense_test_user_base_employee', groups='base.group_user')
        cls.expense_test_user_base_employee_employee = cls.env['hr.employee'].create({
            'name': 'expense_employee',
            'user_id': cls.expense_test_user_base_employee.id,
            'address_home_id': cls.expense_test_user_base_employee.partner_id.id,
            'address_id': cls.expense_test_user_base_employee.partner_id.id,
        })

        # Team approver user & employee
        cls.expense_test_user_team_approver = new_test_user(cls.env, login='expense_test_user_team_approver', groups='hr_expense.group_hr_expense_team_approver')
        cls.expense_test_user_team_approver_employee = cls.env['hr.employee'].create({
            'name': 'expense_team_approver',
            'user_id': cls.expense_test_user_team_approver.id,
            'address_home_id': cls.expense_test_user_team_approver.partner_id.id,
            'address_id': cls.expense_test_user_team_approver.partner_id.id,
        })

        # All-approver user & employee
        cls.expense_test_user_all_approver = new_test_user(cls.env, login='expense_test_user_all_approver', groups='hr_expense.group_hr_expense_user')
        cls.expense_test_user_all_approver_employee = cls.env['hr.employee'].create({
            'name': 'expense_all_approver',
            'user_id': cls.expense_test_user_all_approver.id,
            'address_home_id': cls.expense_test_user_all_approver.partner_id.id,
            'address_id': cls.expense_test_user_all_approver.partner_id.id,
        })

        # Admin user & employee
        cls.expense_test_user_admin = new_test_user(cls.env, login='expense_test_user_admin', groups='hr_expense.group_hr_expense_manager')
        cls.expense_test_user_admin_employee = cls.env['hr.employee'].create({
            'name': 'expense_admin',
            'user_id': cls.expense_test_user_admin.id,
            'address_home_id': cls.expense_test_user_admin.partner_id.id,
            'address_id': cls.expense_test_user_admin.partner_id.id,
        })

        # Other base employee user & employee
        cls.expense_test_user_other_employee_employee = cls.env['hr.employee'].create({
            'address_home_id': cls.env['res.partner'].create({'name': 'expense_other_employee_employee'}).id,
            'name': 'expense_other_employee_employee',
        })
        cls.expense_employee_data = {
            'expense_test_user_portal': cls.expense_test_user_portal,
            'expense_test_user_portal_employee': cls.expense_test_user_portal_employee,
            'expense_test_user_base_employee': cls.expense_test_user_base_employee,
            'expense_test_user_base_employee_employee': cls.expense_test_user_base_employee_employee,
            'expense_test_user_team_approver': cls.expense_test_user_team_approver,
            'expense_test_user_team_approver_employee': cls.expense_test_user_team_approver_employee,
            'expense_test_user_all_approver': cls.expense_test_user_all_approver,
            'expense_test_user_all_approver_employee': cls.expense_test_user_all_approver_employee,
            'expense_test_user_admin': cls.expense_test_user_admin,
            'expense_test_user_admin_employee': cls.expense_test_user_admin_employee,
            'expense_test_user_no_user_employee': cls.expense_test_user_other_employee_employee,
        }


    @users(
        'expense_test_user_portal',
        'expense_test_user_base_employee',
        'expense_test_user_team_approver',
        'expense_test_user_all_approver',
        'expense_test_user_admin',
        )
    def test_expense_access_rights(self):
        """ The expense employee can't be able to create an expense for someone else. """
        current_user = self.env.user
        current_login = current_user.login
        current_employee = self.expense_employee_data[f'{current_login}_employee']
        not_managers = {'expense_test_user_portal', 'expense_test_user_base_employee'}
        managers = {'expense_test_user_team_approver', 'expense_test_user_all_approver'}
        admins = {'expense_test_user_admin'}
        other_employee_expense_vals = {
            'name': "Superboy costume washing",
            'employee_id': self.expense_test_user_other_employee_employee.id,
            'product_id': self.product_a.id,
            'quantity': 1,
            'unit_amount': 1,
        }
        own_expense_vals = {
            'name': "Superboy costume washing",
            'employee_id': current_employee.id,
            'product_id': self.product_a.id,
            'quantity': 1,
            'unit_amount': 1,
        }

        # Test who can create an expense for themselves.
        if current_login == 'expense_test_user_portal':
            with self.assertRaises(AccessError):
                self.env['hr.expense'].create(own_expense_vals)
            own_expense = self.env['hr.expense'].sudo().create(own_expense_vals)
        else:
            own_expense = self.env['hr.expense'].create(own_expense_vals)

        # Test who can create an expense for someone else.
        if current_login in not_managers:
            with self.assertRaises(AccessError):
                self.env['hr.expense'].create(other_employee_expense_vals)
            other_employee_expense = self.env['hr.expense'].sudo().create(other_employee_expense_vals)
        elif current_login == 'expense_test_user_team_approver':  # Special case where the user needs to be the manager of the employee
            with self.assertRaises(AccessError):
                self.env['hr.expense'].create(other_employee_expense_vals)
            self.expense_test_user_other_employee_employee.expense_manager_id = current_user.id
            other_employee_expense = self.env['hr.expense'].create(other_employee_expense_vals)
        else:
            other_employee_expense = self.env['hr.expense'].create(other_employee_expense_vals)

        own_sheet_vals = {
            'name': 'Own Expense Report',
            'expense_line_ids': [Command.set(own_expense.ids)],
        }
        other_employee_sheet_vals = {
            'name': 'Other Employee Expense Report',
            'employee_id': other_employee_expense.employee_id.id,
            'expense_line_ids': [Command.set(other_employee_expense.ids)],
        }
        if current_login == 'expense_test_user_portal':
            with self.assertRaises(AccessError):
                self.env['hr.expense.sheet'].create(own_sheet_vals)
            with self.assertRaises(AccessError):
                self.env['hr.expense.sheet'].create(other_employee_sheet_vals)
            sheets = own_sheet, other_employee_sheet = self.env['hr.expense.sheet'].sudo().create([own_sheet_vals, other_employee_sheet_vals])
        else:
            sheets = own_sheet, other_employee_sheet = self.env['hr.expense.sheet'].sudo().create([own_sheet_vals, other_employee_sheet_vals])

        # Test who can refuse expense reports.
        if current_login in not_managers:
            with self.assertRaises(UserError):
                sheets.refuse_sheet(reason='Because I said so')
            sheets.with_user(self.expense_test_user_admin).refuse_sheet(reason='Because I said so')
        elif current_login in managers:
            with self.assertRaises(UserError):
                own_sheet.refuse_sheet(reason='Because I said so')
            own_sheet.with_user(self.expense_test_user_admin).refuse_sheet(reason='Because I said so')
            other_employee_sheet.refuse_sheet(reason='Because I said so')
        else:
            sheets.refuse_sheet(reason='Because I said so')

        # Test who can reset expense sheets.
        if current_login in not_managers:
            with self.assertRaises(UserError):
                sheets.reset_expense_sheets()
            sheets.with_user(self.expense_test_user_admin).reset_expense_sheets()
        else:
            sheets.reset_expense_sheets()

        # Test who can approve expense reports.
        if current_login in not_managers:
            with self.assertRaises(UserError):
                sheets._check_can_approve()
                sheets._do_approve()
            sheets.with_user(self.expense_test_user_admin)._check_can_approve()
            sheets.with_user(self.expense_test_user_admin)._do_approve()
        elif current_login in managers:
            with self.assertRaises(UserError):
                own_sheet._check_can_approve()
                own_sheet._do_approve()
            own_sheet.with_user(self.expense_test_user_admin)._check_can_approve()
            own_sheet.with_user(self.expense_test_user_admin)._do_approve()
            other_employee_sheet._check_can_approve()
            other_employee_sheet._do_approve()
        else:
            sheets._check_can_approve()
            sheets._do_approve()

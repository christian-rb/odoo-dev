# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.utm.tests.common import TestUTMCommon
from odoo.exceptions import UserError
from odoo.tests.common import tagged, users


@tagged('post_install', '-at_install', 'utm_consistency')
class TestUTMSecurity(TestUTMCommon):

    @users('__system__')
    def test_utm_consistency(self):
        """ You are not supposed to delete the 'utm_medium_email' and
        'utm_medium_website' records as they is hardcoded in
        some functional flows, notably in HR, Mass Mailing and Lead
        Website Form. """

        with self.assertRaises(UserError):
            self.env.ref('utm.utm_medium_email').unlink()
        with self.assertRaises(UserError):
            self.env.ref('utm.utm_medium_website').unlink()

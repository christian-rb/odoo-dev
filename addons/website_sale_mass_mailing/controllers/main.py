# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.http import request, route

from odoo.addons.website_sale.controllers.main import WebsiteSale as WebsiteSaleController


class WebsiteSale(WebsiteSaleController):

    @route()
    def address(self, **kw):
        if 'submitted' in kw and kw.get('newsletter') and request.httprequest.method == 'POST':
            newsletter_id = request.website.newsletter_id
            ContactSubscription = request.env['mailing.subscription'].sudo()
            Contacts = request.env['mailing.contact'].sudo()

            name, email = kw['name'], kw['email']

            subscription = ContactSubscription.search(
                [('list_id', '=', int(newsletter_id)), ('contact_id.email', '=', email)], limit=1)
            if not subscription:
                # inline add_to_list as we've already called half of it
                contact_id = Contacts.search([('email', '=', email)], limit=1)
                if not contact_id:
                    contact_id = Contacts.create({'name': name, 'email': email})
                ContactSubscription.create({'contact_id': contact_id.id,
                                            'list_id': int(newsletter_id)})
            # add email to session
            request.session['mass_mailing_email'] = email
        return super().address(**kw)

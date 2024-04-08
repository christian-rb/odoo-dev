
from .main import technical_page_template
from odoo import http


class IoTBoxTechnicalPage(http.Controller):
    @http.route('/technical', type='http', auth='none', website=True, csrf=False, save_session=False)
    def technical(self):
        return technical_page_template.render({
            'title': "Odoo's IoT Box - Technical",
            'breadcrumb': 'Technical',
        })

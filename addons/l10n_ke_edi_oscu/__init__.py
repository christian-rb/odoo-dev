# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from . import models
from . import wizard


_logger = logging.getLogger(__name__)


def _post_init_hook(env):
    # UNSPSC category codes can be used in Kenya.
    product_unspsc = env['product.unspsc.code'].search([('active', '=', False), ('code', '=ilike', '%00')])
    product_unspsc.active = True

    # Load eTIMS type on the tax
    for company in env['res.company'].search([('chart_template', '=', 'ke')]):
        _logger.info("Company %s already has the Kenyan localization installed, updating...", company.name)
        ChartTemplate = env['account.chart.template'].with_company(company)
        ChartTemplate._load_data({
            'account.tax': ChartTemplate._get_ke_account_tax_etims_type(),
        })

    # Change all OSCU codes ir.model.data to noupdate, so it only gets updated through the cron
    xmls = env['ir.model.data'].search([('model', '=', 'l10n_ke_edi_oscu.code')])
    xmls.write({'noupdate': True})

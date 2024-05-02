# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf_prepare_streams(self, report_ref, data, res_ids=None):
        self.env['account.move']._l10n_pt_compute_missing_hashes()
        return super()._render_qweb_pdf_prepare_streams(report_ref, data, res_ids)

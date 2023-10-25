# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re

from odoo.tools import html_keep_url, misc


def render_sms_notification(text):
    """Transforms plaintext into html making urls clickable and preserving newlines"""
    text_with_links = html_keep_url(str(misc.html_escape(text)))
    return re.sub(r'\r?\n|\r', '<br/>', text_with_links)

# -*- coding: utf-8 -*-

import base64
import logging
from pathlib import Path

from odoo.tools.misc import file_open
from odoo.tools.xml_utils import load_xsd_files_from_url, validate_xml_from_attachment

_logger = logging.getLogger(__name__)

def test_xsd(url=None, path=None, skip=False):
    def decorator(func):
        def wrapped_f(self, *_args):
            if not skip:
                xmls = func(self)
                _validate_xml(self.env, url, path, xmls)
        return wrapped_f
    return decorator

def _validate_xml(env, url, path, xmls):
    # Get the XSD data
    if path:
        file = file_open(path)
        content = file.read()
        attachment_vals = {
            'name': Path(path).name,
            'datas': base64.b64encode(content.encode()),
        }
        xsd_attachment = env['ir.attachment'].create(attachment_vals)
    elif url:
        xsd_attachment = load_xsd_files_from_url(env, url)

    # Validate the XML against the XSD
    if not isinstance(xmls, list):
        xmls = [xmls]

    for xml in xmls:
        validate_xml_from_attachment(env, xml, xsd_attachment.name)

# Quid of error management ?
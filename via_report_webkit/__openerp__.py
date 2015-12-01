# -*- encoding: utf-8 -*-
##############################################################################
#
#    Vikasa Infinity Anugrah, PT
#    Copyright (c) 2011 - 2013 Vikasa Infinity Anugrah <http://www.infi-nity.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

{
    "name": "VIA Report Webkit",
    "version": "1.0",
    "category": "Reporting",
    'complexity': 'easy',
    "description": """
This module hosts all generic tools, utilities, as well as configuration to support
Webkit Report development:
- Generic Images (currently None)
- Enhancement of the Webkit Header to allow for custom page sizes
- Generic Webkit Headers
- Generic Parser with Vikasa Infinity Anugrah's Indonesian Localizations
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    'website': 'http://www.infi-nity.com',
    "depends": [
        "base",
        "via_l10n_id",
        "report_webkit",
        "via_l10n_id",
    ],
    "data": [
        "webkit_header_view.xml",
        "header_images.xml",
        "template_headers.xml",
    ],
    'test': [
    ],
    'demo': [
    ],
    "installable": True,
    "auto_install": False,
#    "certificate": "01436592682591421981",
    'application': False,
    'images': [],
}

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
    "name": "VIA Code Decode",
    "version": "1.2",
    "author": "Vikasa Infinity Anugrah, PT",
    "description": """
This module provide a way to define a user configurable way to fill in selection field.
To use the feature, put a dependency on this module and just call:
    self.pool.get("via.code.decode").get_selection(self, cr, uid, cat_name, company_ids=None, context=None)
passing the Code Category (cat_name) and Company IDs (company_ids).  It will return a list of tuples that are
ready to be used as value in a selection field.
Category Name determines which values are to be pulled out for display.
The values are configurable through the Administration >> Configuration >> Code Decode menu.
Code Category is to be used as cat_name.
Modules can use the field 'pinned' to pin the code and code category.  A 'pinned' code (category) cannot be deleted.
    """,
    "website": "",
    "license": "GPL-3",
    "category": "Tools",
    "depends": ["base"],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        "security/ir.model.access.csv",
        "code_category_view.xml",
        "code_decode_view.xml",
    ],
    "active": False,
    "installable": True,
}

##############################################################################
#
#    Vikasa Infinity Anugrah, PT
#    Copyright (c) 2011 - 2012 Vikasa Infinity Anugrah <http://www.infi-nity.com>
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
    "name": "Cash Advance Management",
    "version": "1.0",
    "author": "Vikasa Infinity Anugrah, PT",
    "category": "Generic Modules/Accounting",
    "description": """
    This module provides cash advance management feature.
    This feature is intended to track cash given to an employee of the company.
    The used cash is usually accounted as the company expense.
    The starting point to track a cash advance is an establishment that is
    made between a company and one of its employee. Before an establishment can
    be created, an account to track the amount of the cash advance needs to be
    configured in the configuration menu.
    """,
    "website" : "http://www.infi-nity.com",
    "license" : "GPL-3",
    "depends": ["account",
                "hr",
                "decimal_precision",
                ],
    "init_xml": [],
    'update_xml': ["security/cash_advance_security.xml",
                   "security/ir.model.access.csv",
                   "cash_advance_establishment_workflow.xml",
                   "cash_advance_establishment_line_workflow.xml",
                   "cash_advance_journal_selection.xml",
                   "cash_advance_establishment.xml",
                   "cash_advance_establishment_line.xml",
                   ],
    'demo_xml': [],
    'installable': True,
    'active': False,
#    'certificate': 'certificate',
}

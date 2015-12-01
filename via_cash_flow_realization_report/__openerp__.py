###############################################################################
#
#  Vikasa Infinity Anugrah, PT
#  Copyright (C) 2012 Vikasa Infinity Anugrah <http://www.infi-nity.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see http://www.gnu.org/licenses/.
#
###############################################################################

{
    "name": "Cash Flow Report",
    "version": "1.0",
    "author": "Vikasa Infinity Anugrah, PT",
    "category": "Generic Modules/Accounting",
    "description": """
    This module provides cash flow report.
    """,
    "website" : "http://www.infi-nity.com",
    "license" : "GPL-3",
    "depends": ["base",
                "jasper_reports",
                "account",
                "decimal_precision",
                "via_financial_reports",
                "via_reporting_tree",
                "via_jasper_report_utils",
                ],
    "init_xml": [],
    'update_xml': ["via_reporting_tree_registration.xml",
                   "wizard/cash_flow_realization_report_view.xml",
                   "report/reporting_service_registration.xml",
                   ],
    'demo_xml': [],
    'installable': True,
    'active': False,
#    'certificate': 'certificate',
}

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
    'name': 'VIA Tax Form',
    'version': '1.4',
    'category': 'Accounting & Finance',
    #'sequence': 19,
    'complexity': 'normal',
    'description': """
    Indonesian Taxform Management Module
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    'website': 'http://www.infi-nity.com',
    #'images' : ['images/purchase_order.jpeg', 'images/purchase_analysis.jpeg', 'images/request_for_quotation.jpeg'],
    'depends': [
        'account',
        'via_partner_enhancements',
        'via_document_signature',
        'via_jasper_report_utils',
        'via_code_decode',
    ],
    'data': [
        'to_be_deleted.xml',
        'account_taxform_data.xml',
        'wizard/account_taxform_create_new_sequence.xml',
        'wizard/account_taxform_select_existing_sequence.xml',
        'wizard/account_invoice_createtaxform.xml',
        'report/account_taxform_report.xml',
        'account_taxform_taxes_view.xml',
        'account_tax_view.xml',
        'account_taxform_view.xml',
        'account_taxform_line_view.xml',
        'account_invoice_view.xml',
        'company_view.xml',
        'account_taxform_reusable_sequences_view.xml',
    ],
    'test': [
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    #'certificate': '0057234283549',
    'application': False,

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

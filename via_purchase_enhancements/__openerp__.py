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
    "name": "Purchase Order Enhancements",
    "version": "1.0",
    "author": "Vikasa Infinity Anugrah, PT",
    "category": "Purchase Management",
    "description": """
    This module provides some enhancements to the existing purchase module:
    - Additional numbering based on PO type that is assigned only when confirmed
      complying with the Indonesian accounting practise
    - Pulling the Notes and Description of the PO line item to the stock move
    - Adding line item notes in purchase requisition and pulling it to PO line item
    - Capability to add (parameterized) references in Purchase Order

    Usage:
    ------
      PO type and numbering:
        * Purchase Order Type of sequences is pre-created by this module
        * Create sequences of Purchase Order Types code
        * Create Purchase Order Type using the sequences
        * 2 fields are added to the PO view, type and number
        * When creating PO, select the PO type (required)
        * Number will be generated when PO is confirmed
      PO Notes and Description in Stock Move:
        * 2 fields are added to the stock move view for reference only
      Purchase Requisition Item Notes:
        * 1 field is added to the Purchase Requisition Item and this line will
          be transferred to the corresponding PO Line Item when a PO is created
      Purchase Order References:
        * Create PO reference type through Purchase Order Parameter menu
        * In the PO form view, a tab is added to add parameter and edit its value
    """,
    "website" : "http://www.infi-nity.com",
    "license" : "GPL-3",
    "depends": [
                "purchase",
                "purchase_requisition",
                "via_code_decode",
                ],
    "init_xml": [
                 "purchase_order_type_data.xml",
                 ],
    'update_xml': [
                   "purchase_parameter.xml",
                   "stock_view.xml",
                   "wizard/via_prorate_discount_view.xml",
                   "purchase_view.xml",
                   "purchase_order_type_view.xml",
                   "purchase_requisition_view.xml",
                   "purchase_view.xml",
                   "security/ir.model.access.csv",
                   ],
    'demo_xml': [],
    'installable': True,
    'active': False,
#    'certificate': 'certificate',
}


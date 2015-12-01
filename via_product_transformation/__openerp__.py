# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 - 2014 Vikasa Infinity Anugrah <http://www.infi-nity.com>
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
    'name': 'Product Transformation',
    'version': '1.32',
    'category': 'Warehouse Management',
    'complexity': 'normal',
    'description': """
        The main purpose of this module is to provide product valuation with lot based valuation (including FIFO and LIFO).
        You can have the following features incorporated.
        * New Cost Methods are introduced FIFO, LIFO and Lot Based.
        * It lets you create valuation/revaluation documents based on the newly added cost methods.
        * It also lets you update the standard_price based on the latest supplier invoice.
        * You can set tracking based on the cost methods.
        * You can add Production Lot in invoice and Cost Price in the production Lot.
        * If stock valuation is being peformed on new cost methods update the cost price based on the lot.
        * Based on costing method FIFO/LIFO creating moves in Delievery Order depends on Production Lot When Sale Order Confirmed
    """,
    'author': 'PT. Vikasa Infinity Anugrah',
    'website': 'http://www.infi-nity.com',
    'depends': [
        'via_lot_valuation'
    ],
    'data': [
        'security/transformation_security.xml',
        'security/ir.model.access.csv',
        'wizard/create_transformation_view.xml',
        'wizard/product_consume_view.xml',
        'wizard/product_trans_enh_view.xml',
        'report/product_transformation_report_view.xml',
        'product_transformation_view.xml',
        'product_trans_sequence.xml',
        'product_transformation_workflow.xml',
        'product_transformation_template_view.xml',
        'product_transformation_template_workflow.xml',
    ],
    'test': [
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

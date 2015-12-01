# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
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
    'name': 'VIA Base Enhancements for OpenERP Stock Modules',
    'version': '1.0',
    'category': 'Warehouse Management',
    #'sequence': 19,
    'complexity': 'easy',
    'description': """
    This module provides enhancements or fixes to the existing base functionalities of OpenERP stock related modules:
    - Incorporate bug-fixes:
      * https://bugs.launchpad.net/openobject-addons/+bug/1015697 (revision 7303 of addons 7.0): Incorrect invoicing from delivery order
      * OPW 600277 (revision 9626 of addons 7.0): Wrong Invoice generated due to product_uos_qty not updated
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    'website': 'http://www.infi-nity.com',
    #'images' : ['images/purchase_order.jpeg', 'images/purchase_analysis.jpeg', 'images/request_for_quotation.jpeg'],
    'depends': ['stock'],
    'data': [
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

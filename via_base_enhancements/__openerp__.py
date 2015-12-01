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
    'name': 'VIA Enhancements for OpenERP Base',
    'version': '1.1',
    'category': 'Hidden/Dependency',
    #'sequence': 19,
    'complexity': 'easy',
    'description': """
    This module provides enhancements or fixes to the existing OpenERP base functionalities:
    - Various utility tools:
      To use this utility, include the following: from via_base_enhancements import tools.resolve_o2m_operations
      * Tool for resolving o2m operations.  It receives various form o2m result and returns
        a dictionary of read result (fields can be specified) of the objects.
        Signature:
            resolve_o2m_operations(cr, uid, target_osv, operations, fields=[], context=None)
        operations format of o2m operation tuple, can be 0, 1, or 4
      * Tool for preparing dictionary returned from orm.read (val) so that it can be used for write.
        It will translate relation fields from tuples to the corresponding id.
        Signature:
            prep_dict_for_write(cr, uid, val, context=None)
      * Tool for preparing dictionary returned from orm.read (val) so that it can be used in Python string formatting operation.
        It will translate relation fields from tuples to the corresponding name and boolean False value to empty string.
        Signature:
            prep_dict_for_formatting(cr, uid, val, context=None)
      * Tool for running a command (popenargs) in terminal and obtaining the stdout output.
        The command line and its argument is passed as a list of strings.
        Signature:
            check_output(*popenargs, **kwargs):
      * Tool for reading a file identified by (path) and return the entire content.
        Signature:
            get_file_content(path='')
      * Tool for writing (content) to temporary file.
        Signature:
            write_temp_file(content='')
      * Tool for purging a given temporary file (path) with a random characters.
        Signature:
            purge_temp_file(path='')
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    'website': 'http://www.infi-nity.com',
    #'images' : ['images/purchase_order.jpeg', 'images/purchase_analysis.jpeg', 'images/request_for_quotation.jpeg'],
    'depends': ['base'],
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

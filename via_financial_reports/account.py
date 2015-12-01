###############################################################################
#
#  Vikasa Infinity Anugrah, PT
#  Copyright (C) 2012 - 2013 Vikasa Infinity Anugrah <http://www.infi-nity.com>
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

try:
    import release
    from osv import fields, osv
    from tools.translate import _
except ImportError:
    import openerp
    from openerp import release
    from openerp.osv import fields, osv
    from openerp.tools.translate import _

class account_account_type(osv.osv):
    _inherit = "account.account.type"
    _columns = {
        'conversion_method': fields.selection([('rpt_rate', 'Reporting Rate'),
                                               ('trx_rate', 'Transactional Rate')],
                                              'Conversion Method'),
    }

account_account_type()

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

from osv import fields, osv


class account_account(osv.osv):
    _inherit = 'account.account'

    _columns = {
        'invoice_realisation_account_id': fields.many2one(string='Invoice Tax Realisation Account', obj='account.account'),
        'refund_realisation_account_id': fields.many2one(string='Refund Tax Realisation Account', obj='account.account'),
        'invoice_realisation_journal_id': fields.many2one(string='Invoice Tax Realisation Journal', obj='account.journal'),
        'refund_realisation_journal_id': fields.many2one(string='Refund Tax Realisation Journal', obj='account.journal'),
    }

account_account()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

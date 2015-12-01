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

from osv import osv


class account_invoice_createtaxform(osv.osv_memory):
    """
    This wizard will create the taxform of all the selected validated invoices
    """
    _name = "account.invoice.createtaxform"
    _description = "Create the taxforms for the selected invoices"

    def create_taxforms(self, cr, uid, ids, context=None):
        self.pool.get('account.invoice.tax').create_taxform(cr, uid, context.get('active_ids', []), context=context)
        return {'type': 'ir.actions.act_window_close'}

account_invoice_createtaxform()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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
from tools.translate import _
from osv import fields
from via_account_taxform.account_taxform import account_taxform


class account_taxform_select_existing_sequence(osv.osv_memory):
    """
    This wizard allow user to manually choose from existing taxform sequences
    """

    _name = "account.taxform.select_existing_sequence"
    _description = "Create the taxforms for the selected invoices"

    def _default_company(self, cr, uid, context=None):
        res = False
        _taxform_id = context.get('active_taxform', False)
        if _taxform_id:
            res = self.pool.get('account.taxform').browse(cr, uid, _taxform_id, context=context).company_id.id
        return res

    _columns = {
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
        'reusable_id': fields.many2one('account.taxform.reusable.sequences', 'Reused ID', required=True),
        'trx_code': fields.char('Transaction Code', size=3),
        'branch_code': fields.selection(account_taxform._columns['branch_code'].selection, 'Branch Code'),
    }

    _defaults = {
        'company_id': _default_company,
    }

    def select_existing_sequence(self, cr, uid, ids, context=None):
        if len(context.get('active_ids', [])) > 1:
            raise osv.except_osv('Warning', 'Only one taxform can be processed at a time!')
        _taxform_id = context.get('active_id', False)
        if not _taxform_id:
            raise osv.except_osv('Warning', 'No taxform is selected!')

        data = self.pool.get('account.taxform.select_existing_sequence').browse(cr, uid, ids[0], context=context)

        _reusable = data.reusable_id
        _vals = {
            'taxform_id': _reusable.taxform_sequence,
            'trx_code': data.trx_code,
            'branch_code': data.branch_code,
        }
        self.pool.get('account.taxform').write(cr, uid, _taxform_id, _vals, context=context)
        _reusable.write({'reusable': False}, context=context)

        rv = {
            'name': _("Taxform"),
            'res_id': _taxform_id,
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'account.taxform',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': context
        }

        return rv

account_taxform_select_existing_sequence()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

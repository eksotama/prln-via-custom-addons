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

import netsvc
from osv import fields, osv
import decimal_precision as dp
from via_base_enhancements.tools import prep_dict_for_write


class account_taxform_line(osv.osv):
    _name = "account.taxform.line"
    _description = "Tax Line"
    logger = netsvc.Logger()

    def _amount_untaxed(self, cr, uid, ids, name, args, context=None):
        res = {}
        for _obj in self.browse(cr, uid, ids, context=context):
            res[_obj.id] = _obj.price_unit * _obj.quantity

        return res

    _columns = {
        'taxform_id': fields.many2one('account.taxform', 'Taxform ID', readonly=True),
        'invoice_line_id': fields.many2one('account.invoice.line', 'Invoice Line ID', readonly=True),
        'name': fields.char('Description', size=256),
        'product_id': fields.related('invoice_line_id', 'product_id', type="many2one", relation='product.product', store=True, string='Product ID'),
        'price_unit': fields.related('invoice_line_id', 'price_unit', string='Price Unit', type="float", store=True, digits_compute=dp.get_precision('Account')),
        'quantity': fields.related('invoice_line_id', 'quantity', string='Quantity', type="float", store=True),
        'uom': fields.related('invoice_line_id', 'uos_id', 'name', string='UoM', type="char", size=64, store=True),
        'discount': fields.related('invoice_line_id', 'discount', string='Discount', type="float", store=True, digits_compute=dp.get_precision('Account')),
        'price_subtotal': fields.float('Subtotal', digits_compute=dp.get_precision('Account')),
        'amount_untaxed': fields.function(_amount_untaxed, digits_compute=dp.get_precision('Account'), string='Untaxed')
    }

    def get_invoice_info(self, cr, uid, invoice_line_ids, context=None):
        res = {}
        if not context:
            context = {}
        if isinstance(invoice_line_ids, (list, tuple, dict, )):
            select = list(invoice_line_ids)
        else:
            select = [invoice_line_ids]

        _cols = self._columns.keys()
        for _obj in self.pool.get('account.invoice.line').read(cr, uid, select, _cols, context=context):
            _obj_id = _obj['id']
            _obj = prep_dict_for_write(cr, uid, _obj, context=context)
            res[_obj_id] = _obj.copy()

        return isinstance(invoice_line_ids, (int, long, )) and res[invoice_line_ids] or res

    def create(self, cr, uid, vals, context=None):
        _invoice_info = self.get_invoice_info(cr, uid, vals['invoice_line_id'], context=context)
        vals.update(_invoice_info)
        return super(account_taxform_line, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if 'invoice_line_id' in vals:
            res = {}
            if not context:
                context = {}
            if isinstance(ids, (list, tuple, dict, )):
                select = list(ids)
            else:
                select = [ids]

            for _obj in self.pool.get('account.invoice.line').browse(cr, uid, select, context=context):
                _val = vals.copy()
                if _obj.invoice_line_id:
                    _invoice_info = self.get_invoice_info(cr, uid, _obj.invoice_line_id.id, context=context)
                    _val.update(_invoice_info)
                res = super(account_taxform_line, self).write(cr, uid, _obj.id, _val, context=context)
        else:
            res = super(account_taxform_line, self).write(cr, uid, ids, vals, context=context)

        return res

account_taxform_line()

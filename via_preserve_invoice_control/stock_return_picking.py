# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 - 2015 Vikasa Infinity Anugrah <http://www.infi-nity.com>
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

from osv import osv, fields


class stock_return_picking(osv.osv_memory):
    _inherit = "stock.return.picking"

    def create_returns(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        record_id = context.get('active_id', False)
        pick_obj = self.pool.get('stock.picking')
        pick = pick_obj.browse(cr, uid, record_id, context=context)
        _pick_inv_state = pick.invoice_state
        _pick_type = pick.type
        res = super(stock_return_picking, self).create_returns(cr, uid, ids, context=context)
        if (_pick_inv_state in ['2binvoiced', 'invoiced']) and (_pick_type in ['out', 'in', 'internal']):
            pick.write({'invoice_state': _pick_inv_state}, context=context)
        return res

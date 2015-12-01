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

from osv import osv, fields
import decimal_precision as dp
from tools.translate import _
import logging


_logger = logging.getLogger(__name__)


class product_consume(osv.osv_memory):
    _name = 'product.consume'

    def _is_loc_selected(self, cr, uid, ids, name, args, context=None):
        '''
        Conveys whether Location is selected in the parent Product Transformation
        --------------------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        '''
        if not context:
            context = {}
        _ils = context.get('location_selected', False)
        res = {}
        for _obj in self.browse(cr, uid, ids, context=context):
            res[_obj.id] = _ils
        return res

    _columns = {
        'prod_trans_id': fields.many2one('product.transformation', 'Product Transformation'),
        'product_id': fields.many2one('product.product', 'Product', required=True, domain=[('type', '!=', 'service')]),
        'product_uom_id': fields.many2one('product.uom', 'UoM', required=True, domain="[('category_id', '=', product_uom_categ_id)]"),
        'product_qty': fields.float('Qty', digits_compute=dp.get_precision('Product UoM'), required=True),
        'raw_loc_id': fields.many2one('stock.location', 'Location', domain="[('usage', '=', 'internal')]"),
        'prodlot_id': fields.many2one('stock.production.lot', 'Lot #', domain="[('product_id', '=', product_id)]"),
        'consume_date': fields.date('Date'),
        'is_loc_selected': fields.function(_is_loc_selected, 'Is Location Selected ?', type='boolean'),
        'is_lot_based': fields.related('product_id', 'is_lot_based', type='boolean', string='Product Is Lot Based? '),
        'is_auto_assign': fields.related('product_id', 'is_auto_assign', type='boolean', string='Product Is Auto Assign?'),
    }

    _defaults = {
        'product_qty': lambda * a: 1.0,
        'is_loc_selected': lambda self, cr, uid, c: c.get('location_selected', False) and True,
        'prod_trans_id': lambda self, cr, uid, c: c.get('active_id', False),
        'is_lot_based': lambda *a: False,
        'is_auto_assign': lambda *a: False,
    }

    def onchange_product_id(self, cr, uid, ids, *args, **kwargs):
        return self.pool.get('product.consume.line').onchange_product_id(cr, uid, ids, *args, **kwargs)

    def check_avail_stock_lot(self, cr, uid, ids, *args, **kwargs):
        return self.pool.get('product.consume.line').check_avail_stock_lot(cr, uid, ids, *args, **kwargs)

    def get_product_to_consume(self, cr, uid, ids, context=None):
        prod_cons_line_obj = self.pool.get('product.consume.line')

        for wiz_consume in self.browse(cr, uid, ids, context=context):
            # Localized variables
            _vals = self.copy_data(cr, uid, wiz_consume.id, context=context)

            # Do not save Product Transformation's Raw Location ID if none is given
            if _vals.get('raw_loc_id', False):
                del _vals['raw_loc_id']

            prod_cons_line_obj.create(cr, uid, _vals, context)

        return {'type': 'ir.actions.act_window_close'}

product_consume()

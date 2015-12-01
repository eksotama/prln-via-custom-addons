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
import tools
import decimal_precision as dp


class report_product_transformation(osv.osv):
    _name = 'report.product.transformation'
    _auto = False

    def _get_product_transformation_states(self, cr, uid, context=None):
        return self.pool.get('product.transformation')._columns['state'].selection

    _columns = {
        'name': fields.char('Transformation', size=32),
        'state': fields.selection(_get_product_transformation_states, string="State"),
        'c_product_id': fields.many2one('product.product', 'Consumed Product'),
        'c_uom_id': fields.many2one('product.uom', 'Consumed Product UoM'),
        'c_product_qty': fields.float('Consumed Qty', digits_compute=dp.get_precision('Purchase Price')),
        'c_prod_lot_id': fields.many2one('stock.production.lot', 'Consumed Lot #'),
        'f_product_id': fields.many2one('product.product', 'Finished Product'),
        'f_uom_id': fields.many2one('product.uom', 'Finished Product UoM'),
        'f_product_qty': fields.float('Finished Qty'),
        'f_prod_lot_id': fields.many2one('stock.production.lot', 'Finished Lot #'),
    }

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'report_product_transformation')
        cr.execute("""
            CREATE view report_product_transformation as
                SELECT
                ROW_NUMBER() OVER (ORDER BY t.id ASC) AS id,
                    t.name as name,
                    c.product_id as c_product_id,
                    c.product_uom_id as c_uom_id,
                    c.prodlot_id as c_prod_lot_id,
                    c.product_qty as c_product_qty,
                    f.product_qty as f_product_qty,
                    f.prodlot_id as f_prod_lot_id,
                    f.product_id as f_product_id,
                    f.product_uom_id as f_uom_id,
                    t.state as state
                FROM
                    product_transformation t,
                    finish_goods_line f,
                    product_consume_line c
                WHERE
                    t.id = c.prod_trans2_id AND
                    f.prod_trans_id = t.id
              """)

report_product_transformation()

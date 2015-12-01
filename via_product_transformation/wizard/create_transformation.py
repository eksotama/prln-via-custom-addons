# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 - 2013 Vikasa Infinity Anugrah <http: //www.infi-nity.com>
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
#    along with this program.  If not, see http: //www.gnu.org/licenses/.
#
##############################################################################

from osv import osv, fields
from tools.translate import _


class create_transformation(osv.osv_memory):
    _name = 'create.transformation'
    _description = 'Wizard to create transformation'

    _columns = {
        'prod_trans_tmpl_id': fields.many2one('product.transformation.template', 'Transformation Template', help='Template based on which you need to create Product Transformation'),
        'quantity': fields.integer('#Transformations', help='No of transformations to be created based on the selected template')
    }

    _defaults = {
        'prod_trans_tmpl_id': lambda self, cr, uid, context: context.get('active_id', False),
        'quantity': lambda *a: 1
    }

    def create_transformation(self, cr, uid, ids, context=None):
        """
        This method creates transformations based on the product transformation
        """
        # It is assumed that only 1 wizard exist at any point of time for each session
        wiz = self.browse(cr, uid, ids[0], context=context)

        # Get the Vals for Transformation
        _ptt = wiz.prod_trans_tmpl_id
        trans_vals = _ptt.prepare_instance(context=context).get(_ptt.id, {})

        _pt_pool = self.pool.get('product.transformation')
        _pcl_pool = self.pool.get('product.consume.line')
        _fgl_pool = self.pool.get('finish.goods.line')
        for i in range(int(wiz.quantity)):
            _to_write = trans_vals.copy()
            # Create Transformation
            _consume_line_ids = []
            if 'consume_line_ids' in _to_write:
                _consume_line_ids = _to_write.pop('consume_line_ids')
            _finish_goods_line_ids = []
            if 'finish_goods_line_ids' in _to_write:
                _finish_goods_line_ids = _to_write.pop('finish_goods_line_ids')
            trans_id = _pt_pool.create(cr, uid, _to_write, context=context)

            # Add Products to Consume Lines in Transformation
            for c_line in _consume_line_ids:
                _c_line_to_write = c_line.copy()
                _c_line_to_write.update({'prod_trans_id': trans_id})
                _pcl_pool.create(cr, uid, _c_line_to_write, context=context)

            # Add Finished Goods Products in Trnansformation
            for f_line in _finish_goods_line_ids:
                _f_line_to_write = f_line.copy()
                _f_line_to_write.update({'prod_trans_id': trans_id})
                _ctx = context.copy()
                _ctx.update({'recalculate_mp': False})
                _fgl_pool.create(cr, uid, _f_line_to_write, context=_ctx)
        return {'type': 'ir.actions.act_window_close'}

create_transformation()

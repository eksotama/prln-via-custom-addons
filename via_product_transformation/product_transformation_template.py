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
from via_base_enhancements.tools import prep_dict_for_write
import decimal_precision as dp


class product_transformation_template(osv.osv):
    _name = 'product.transformation.template'
    _description = 'Product Transformation Template'

    _columns = {
        'name': fields.char('Name', size=128, help='The Product Transformation Name that will be used in the Reference of Transformation when creating a transformation from a template', required=True),
        'trans_loc_id': fields.many2one('stock.location', 'Transformation Location', help='Location where products converted. Used as Transformation Location source value on Product Transformation Document.', required=True),
        'stock_journal_id': fields.many2one('stock.journal', 'Stock Journal', help='Used as Stock Journal source value on Product Transformation Document'),
        'raw_loc_id': fields.many2one('stock.location', 'Raw Material Source Location', help='Used as Raw Material Source Location source value on Product Transformation Document.'),
        'prod_cons_ids': fields.one2many('prod.cons.tmpl.line', 'prod_trans_tmpl_id', 'Products to Consume', help='Used as Products to Consume table source value on Product Transformation Document'),
        'finish_loc_id': fields.many2one('stock.location', 'Finished Goods Location', help='Location where finished good is produced'),
        'finish_goods_ids': fields.one2many('finish.goods.tmpl.line', 'prod_trans_tmpl1_id', 'Finished Goods', help='Used as Finished Goods table source value on Product Transformation Document'),
        'responsible_id': fields.many2one('res.users', 'Responsible', help='Responsible Person'),
        'company_id': fields.many2one('res.company', 'Company', helP='Company', required=True),
        'memo': fields.text('Memo', help='Memo to write any notes regarding the Transformation'),
        'state': fields.selection([('draft', 'Draft'), ('cancel', 'Cancelled'), ('submit', 'Submitted'), ('available', 'Available'), ('inactive', 'Inactive')], 'State', readonly=True),
    }

    _defaults = {
        'responsible_id': lambda self, cr, uid, ctx: uid,
        'state': lambda *a: 'draft',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
    }

    def prepare_instance(self, cr, uid, ids, context=None):
        """
        This method will create an instance of product.transformation based on the given information
        -----------------------------------------------------------
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current Logged in User
        @return : A dictionary ready to be passed to write method
        """
        res = {}
        for _obj in self.browse(cr, uid, ids, context=context):
            _vals = _obj.read(context=context)[0]
            'prod_cons_ids', 'finish_goods_ids'
            _vals = prep_dict_for_write(cr, uid, _vals, context=context)
            _vals.update({
                'reference': _vals.get('name', ''),
                'raw_src_loc_id': _vals.get('raw_loc_id', False),
                'finish_goods_loc_id': _vals.get('finish_loc_id', False),
                'trans_tmpl_id': _obj.id,
            })

            for _key in ['name', 'raw_loc_id', 'state', 'prod_cons_ids', 'finish_goods_ids']:
                if _key in _vals:
                    del _vals[_key]

            _ctx = context.copy()
            _ctx.update({'raw_loc': bool(_obj.raw_loc_id)})
            _vals.update({'consume_line_ids': [line.prepare_instance(context=_ctx).get(line.id, {}) for line in _obj.prod_cons_ids]})

            _ctx = context.copy()
            _ctx.update({'finished_loc': bool(_obj.raw_loc_id)})
            _vals.update({'finish_goods_line_ids': [line.prepare_instance(context=_ctx).get(line.id, {}) for line in _obj.finish_goods_ids]})

            res.setdefault(_obj.id, _vals)
        return res

product_transformation_template()


class prod_cons_tmpl_line(osv.osv):
    _name = 'prod.cons.tmpl.line'
    _description = 'Products to Consume(Template)'
    _rec_name = 'product_id'

    def _is_loc_selected(self, cr, uid, ids, name, args, context=None):
        '''
        Conveys whether Location is selected in the parent Product Transformation Template
        --------------------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        '''
        if context is None:
            context = {}
        _ils = context.get('location_selected', False)
        res = {}
        for _obj in self.browse(cr, uid, ids, context=context):
            res[_obj.id] = _ils
        return res

    _columns = {
        'prod_trans_tmpl_id': fields.many2one('product.transformation.template', 'Product Transformation Template', help='Template for Product Transformation'),
        'product_id': fields.many2one('product.product', 'Product', help='Products to be consumed', domain=[('type', '<>', 'service')]),
        'qty': fields.float('Quantity', digits_compute=dp.get_precision('Product UoM'), help='Quantity of product to be consumed.'),
        'product_uom_id': fields.many2one('product.uom', 'UoM', help="Quantity's UoM"),
        'raw_loc_id': fields.many2one('stock.location', 'Raw Material Location', help='Raw Material Source Location'),
        'is_loc_selected': fields.function(_is_loc_selected, 'Is Location Selected ?', type='boolean'),
    }

    _defaults = {
        'qty': lambda *a: 1.0,
        'is_loc_selected': lambda c, u, i, ctx={}: ctx.get('location_selected', False),
    }

    def onchange_product_id(self, cr, uid, ids, product_id, context=None):
        """
        This method is usef to get the product UoM from the Product
        -----------------------------------------------------------
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current Logged in User
        @param product_id : The product to be consumed
        @return : A dictionary having 'value' as key and a dictionary having field,value pair as value
        """
        res = {}
        product = product_id and self.pool.get('product.product').browse(cr, uid, product_id) or False
        res['value'] = {'product_uom_id': product and product.uom_po_id and product.uom_po_id.id or False}
        return res

    def prepare_instance(self, cr, uid, ids, context=None):
        """
        This method will create an instance of product.consume.line based on the given information
        -----------------------------------------------------------
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current Logged in User
        @return : A dictionary ready to be passed to write method
        """
        res = {}
        for _obj in self.browse(cr, uid, ids, context=context):
            _pid = _obj.product_id and _obj.product_id.id or False
            _vals = {
                'product_id': _pid,
                'product_qty': _obj.qty,
                'raw_loc_id': _obj.raw_loc_id and _obj.raw_loc_id.id or False,
            }
            _vals.update(_obj.onchange_product_id(_pid).get('value', {}))
            res.setdefault(_obj.id, _vals)
        return res

prod_cons_tmpl_line()


class finish_goods_tmpl_line(osv.osv):
    _name = 'finish.goods.tmpl.line'
    _description = 'Finished Goods(Template)'
    _rec_name = 'product_id'

    def _is_loc_selected(self, cr, uid, ids, name, args, context=None):
        '''
        Conveys whether Location is selected in the parent Product Transformation Template
        --------------------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        '''
        if context is None:
            context = {}
        _ils = context.get('location_selected', False)
        res = {}
        for _obj in self.browse(cr, uid, ids, context=context):
            res[_obj.id] = _ils
        return res

    _columns = {
        'prod_trans_tmpl1_id': fields.many2one('product.transformation.template', 'Product Transformation Template', help='Template for Product Transformation'),
        'product_id': fields.many2one('product.product', 'Product', help='Products produced from this document', domain=[('type', '<>', 'service')]),
        'qty': fields.float('Quantity', digits_compute=dp.get_precision('Product UoM'), help='Quantity of produced products'),
        'product_uom_id': fields.many2one('product.uom', 'UoM', help="Quantity's UoM"),
        'finish_loc_id': fields.many2one('stock.location', 'Finish Goods Location', help='Finish Goods Storage Location'),
        'material_usage_per': fields.float('Material Usage Percentage', digits_compute=dp.get_precision('Purchase Price'), help='% of the material used'),
        'is_loc_selected': fields.function(_is_loc_selected, 'Is Location Selected ?', type='boolean'),
    }

    _defaults = {
        'qty': lambda *a: 1.0,
        'is_loc_selected': lambda c, u, i, ctx={}: ctx.get('location_selected', False),
    }

    def onchange_product_id(self, cr, uid, ids, product_id, context=None):
        """
        This method is usef to get the product UoM from the Product
        -----------------------------------------------------------
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current Logged in User
        @param product_id : The product to be consumed
        @return : A dictionary having 'value' as key and a dictionary having field,value pair as value
        """
        res = {}
        product = product_id and self.pool.get('product.product').browse(cr, uid, product_id) or False
        res['value'] = {'product_uom_id': product and product.uom_id and product.uom_id.id or False}
        return res

    def prepare_instance(self, cr, uid, ids, context=None):
        """
        This method will create an instance of finish.goods.line based on the given information
        -----------------------------------------------------------
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current Logged in User
        @return : A dictionary ready to be passed to write method
        """
        res = {}
        for _obj in self.browse(cr, uid, ids, context=context):
            _pid = _obj.product_id and _obj.product_id.id or False
            _vals = {
                'product_id': _pid,
                'product_qty': _obj.qty,
                'finish_goood_loc_id': _obj.finish_loc_id and _obj.finish_loc_id.id or False,
                'material_usage_per': _obj.material_usage_per,
                'cost_amount': 0.0,
            }
            _vals.update(_obj.onchange_product_id(_pid).get('value', {}))
            res.setdefault(_obj.id, _vals)
        return res

finish_goods_tmpl_line()

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
import decimal_precision as dp
import time
from tools import DEFAULT_SERVER_DATE_FORMAT
from tools.translate import _
from tools import float_compare, float_round
import netsvc
from via_lot_valuation.product import LOT_BASED_METHODS
import logging


TRANS_STATES = [
    ('draft', 'Draft'),
    ('cancel', 'Cancelled'),
    ('consumption', 'Consumed'),
    ('ready', 'Ready'),
    ('done', 'Finished')
]


def calc_usage(cr, qty=0.0, total_qty=1.0, total_cost=0.0, cost_amount=0.0, reverse_calc=False, recalculate_mp=True, original_mp=0.0):
    if reverse_calc:
        if total_cost:
            # Calculate material_usage_per from cost_amount and total_cost
            res = {
                'material_usage_per': float_round(total_cost and (float(cost_amount) / float(total_cost) * 100.0) or 0.0, precision_digits=dp.get_precision('Purchase Price')(cr)[1]),
                'cost_amount': float_round(cost_amount, precision_digits=dp.get_precision('Purchase Price')(cr)[1]),
            }
        else:
            res = {}
    else:
        # Calculate cost_amount from the given qty, total_qty, total_cost, or original_mp
        _mup = original_mp
        if recalculate_mp:
            _mup = total_qty and (float(qty) * 100.0 / float(total_qty)) or 0.0
        res = {
            'material_usage_per': float_round(_mup, precision_digits=dp.get_precision('Purchase Price')(cr)[1]),
            'cost_amount': float_round(_mup * float(total_cost) / 100.0, precision_digits=dp.get_precision('Purchase Price')(cr)[1]),
        }
    return res


class product_transformation(osv.osv):
    _name = 'product.transformation'
    _description = 'Product Transformation'

    def _get_totals(self, cr, uid, ids, field_name, arg, context=None):
        """
        This method calculates:
        * total cost from the finish goods lines
        * total material usage percentage from the finish goods lines
        * total cost
        -------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param ids: Current Records
        @param name: Functional field's name
        @param args: Other arguments
        @param context: standard Dictionary
        @return: Dictionary having identifier of the record as key and the total cost as value
        """
        res = {}
        for _obj in self.browse(cr, uid, ids, context=context):
            res[_obj.id] = {
                'total_cost': 0.0,
                'total_finish_cost': 0.0,
                'total_material_usage_per': 0.0,
            }
            total = 0.0
            total_cost = 0.0
            total_material_usage_per = 0.0
            for line in _obj.finish_goods_line_ids:
                total_cost += float_round(line.cost_amount, precision_digits=dp.get_precision('Purchase Price')(cr)[1])
                total_material_usage_per += float_round(line.material_usage_per, precision_digits=dp.get_precision('Purchase Price')(cr)[1])
            res[_obj.id]['total_finish_cost'] = total_cost
            res[_obj.id]['total_material_usage_per'] = total_material_usage_per

            for prod_cons in _obj.consumed_line_ids:
                if prod_cons.product_id.is_lot_based:
                    _price = prod_cons.prodlot_id and prod_cons.prodlot_id.cost_price_per_unit or 0.0
                else:
                    _price = prod_cons.product_id and prod_cons.product_id.standard_price or 0.0

                total += _price * prod_cons.product_qty
            res[_obj.id]['total_cost'] = float_round(total, precision_digits=dp.get_precision('Purchase Price')(cr)[1])

        return res

    def _get_to_consume_by_lot(self, cr, uid, ids, xcld_line=[], context=None):
        res = {}
        select = (isinstance(ids, (int, long)) and [ids]) or ids
        select = map(lambda x: isinstance(x, dict) and x['id'] or x, select)

        _uom_pool = self.pool.get('product.uom')
        _qty_by_lot = {}
        for _obj in self.browse(cr, uid, select, context=context):
            for _line in _obj.consume_line_ids:
                if _line.id in xcld_line:
                    continue

                _spl = _line.prodlot_id
                if _spl:
                    _prd_obj = _spl.product_id
                    if _prd_obj and _line.product_uom_id:
                        if _line.product_uom_id.factor != _prd_obj.uom_id.factor:
                            _base_line_qty = _uom_pool._compute_qty_obj(cr, uid, _line.product_uom_id, _line.product_qty, _prd_obj.uom_id, context=context)
                        else:
                            _base_line_qty = _line.product_qty
                        _qty_by_lot.update({_spl.id: _base_line_qty + _qty_by_lot.setdefault(_spl.id, 0.0)})

            res.update({_obj.id: _qty_by_lot})
        return res

    _columns = {
        'name': fields.char('Product Transformation No.', size=64, required=True),
        'date': fields.date('Date', required=True),
        'reference': fields.char('Reference', size=64),
        'trans_loc_id': fields.many2one('stock.location', 'Transformation Location', required=True),
        'stock_journal_id': fields.many2one('stock.journal', 'Stock Journal'),
        'raw_src_loc_id': fields.many2one('stock.location', 'Raw Material Source Location'),
        'state': fields.selection(TRANS_STATES, string="State"),
        'consume_line_ids': fields.one2many('product.consume.line', 'prod_trans_id', 'Products to Consume'),
        'consumed_line_ids': fields.one2many('product.consume.line', 'prod_trans2_id', 'Consumed Products'),
        'finish_goods_loc_id': fields.many2one('stock.location', 'Finished Goods Storage Location'),
        'finish_goods_line_ids': fields.one2many('finish.goods.line', 'prod_trans_id', 'Finished Goods'),
        'total_cost': fields.function(_get_totals, string='Total Cost', digits_compute=dp.get_precision('Purchase Price'), multi='totals'),
        'responsible_id': fields.many2one('res.users', 'Responsible'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'memo': fields.text('Memo'),
        'total_finish_cost': fields.function(_get_totals, string='Total Finish Cost', digits_compute=dp.get_precision('Purchase Price'), multi='totals'),
        'total_material_usage_per': fields.function(_get_totals, string="Total Material Usage", digits_compute=dp.get_precision('Purchase Price'), multi='totals'),
        'trans_tmpl_id': fields.many2one('product.transformation.template', 'Transformation Template')
    }

    def _check_total_cost(self, cr, uid, ids, context=None):
        """
        It checks the total cost and the total of cost amounts of the finished goods line is equal or not.
        --------------------------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param ids: Identifier(s) of Current record(s)
        @param context: Standard Dictionary
        @return: True or False
        """
        for _obj in self.browse(cr, uid, ids, context=context):
            if _obj.finish_goods_line_ids and float_compare(_obj.total_finish_cost, _obj.total_cost, precision_rounding=0.005):
                return False
        return True

    def _check_total_material_per(self, cr, uid, ids, context=None):
        """
        It checks the total material usage percentage is equal to 100 or not.
        ---------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param ids: Identifier(s) of Current record(s)
        @param context: Standard Dictionary
        @return: True or False
        """
        for _obj in self.browse(cr, uid, ids, context=context):
            if _obj.finish_goods_line_ids and float_compare(_obj.total_material_usage_per, 100.0, precision_rounding=0.005):
                return False
        return True

    _constraints = [
        (_check_total_cost, 'The sum of Cost Amount of all Finished Goods Lines must be equal to the Total Finish Cost of the Product Transformation.', ['total_finish_cost']),
        (_check_total_material_per, 'The sum of Material Usage Percentage of all Finished Goods Lines must be equal to 100.', ['total_material_usage_per']),
    ]

    def _get_fg_qty_total(self, cr, uid, ids, exclude_ids=[], context=None):
        '''
        Calculate the total of Finished Good Line's Product Quantity except those in exclude_ids
        --------------------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param ids: Selected Record ID
        @param exclude_ids: List of excluded Finished Good Line IDs
        @returns: The calculated total per Product Transformation
        '''
        res = {}
        select = (isinstance(ids, (int, long)) and [ids]) or ids
        select = map(lambda x: isinstance(x, dict) and x['id'] or x, select)

        for _obj in self.browse(cr, uid, select, context=context):
            # Get the quantity of all lines that are not part of the modified lines
            _fg_qty_list = [float_round(line.product_qty, precision_digits=dp.get_precision('Purchase Price')(cr)[1]) or 0.0 for line in _obj.finish_goods_line_ids if line.id not in exclude_ids]
            res[_obj.id] = float_round(sum(_fg_qty_list), precision_digits=dp.get_precision('Purchase Price')(cr)[1])

        return res

    def recalc_fg_values(self, cr, uid, ids, mod_lines={}, recalculate_mp=True, context=None):
        '''
        Recalculate the Material Usage Percentage and Cost Amount of the Finished Goods of the given
        Product Transformation except for the given mod_line which will be valued at mod_qty
        The last Material Usage Percentage and Cost Amount per object will be adjusted to make the
        total valid for the _constraints above
        --------------------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param ids: Selected Record ID
        @param mod_line: A dictionary containing the IDs of the Product Transformation with the value of
            another dictionary that contains the IDs of Finished Goods Line that is changed and to be
            'excluded' in calculation with the value to be used in place e.g.
            {
                'pt_1_id': {'pt_1_fg_1_id': 0.0, 'pt_1_fg_2_id': 10.0, },
                'pt_2_id': {'pt_2_fg_1_id': 5.0, },
            }
        @param recalculate_mp: A flag whether material_usage_per is to be re-calculated or not
        @returns: A dictionary containing the Material Usage Percentage and Cost Amount per Finsihed Good Line
            in the following format:
            {
                'pt_1_id': {'pt_1_fg_1_id': {'material_usage_per': 50.0, 'cost_amount': 10.0, }, 'pt_1_fg_2_id': {'material_usage_per': 50.0, 'cost_amount': 10.0, }, },
                'pt_2_id': {'pt_2_fg_1_id': {'material_usage_per': 100.0, 'cost_amount': 10.0, }, },
            }
        '''
        res = {}
        select = (isinstance(ids, (int, long)) and [ids]) or ids
        select = map(lambda x: isinstance(x, dict) and x['id'] or x, select)

        for _obj in self.browse(cr, uid, select, context=context):
            _pt_mod_lines = mod_lines.get(_obj.id, {})
            _pt_mod_line_ids = _pt_mod_lines.keys()

            # Get the quantity of all lines that are not part of the modified lines
            prod_qty_total = _obj._get_fg_qty_total(exclude_ids=_pt_mod_line_ids, context=context).get(_obj.id, 0.0)

            # Add the values to be used in place
            for _mod_line in _pt_mod_lines:
                prod_qty_total += float_round(_pt_mod_lines.get(_mod_line, 0.0), precision_digits=dp.get_precision('Purchase Price')(cr)[1])

            # Recalculate the material_usage_per and cost_amount
            res[_obj.id] = {}
            _mup_agg = 0.0
            _cam_agg = 0.0
            _line = False
            for _line in _obj.finish_goods_line_ids:
                if _line.id not in _pt_mod_line_ids:
                    res[_obj.id][_line.id] = calc_usage(cr, _line.product_qty, prod_qty_total, _obj.total_cost, recalculate_mp=recalculate_mp, original_mp=_line.material_usage_per)
                    _mup_agg += float_round(res[_obj.id][_line.id]['material_usage_per'], precision_digits=dp.get_precision('Purchase Price')(cr)[1])
                    _cam_agg += float_round(res[_obj.id][_line.id]['cost_amount'], precision_digits=dp.get_precision('Purchase Price')(cr)[1])
            # Last line must make the MUP and Cost Amount valid according to the _constraints above
            if _line and recalculate_mp:
                res[_obj.id][_line.id]['material_usage_per'] += float_round(100.00 - _mup_agg, precision_digits=dp.get_precision('Purchase Price')(cr)[1])
                res[_obj.id][_line.id]['cost_amount'] += float_round(_obj.total_cost - _cam_agg, precision_digits=dp.get_precision('Purchase Price')(cr)[1])
            else:
                pass

        return res

    def update_fg_values(self, cr, uid, ids, recalculate_mp=True, context=None):
        '''
        Recalculate and save the Material Usage Percentage and Cost Amount of the Finished Goods Lines
        --------------------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param ids: Selected Record ID
        @param mod_line: A dictionary containing the IDs of the Product Transformation with the value of
            another dictionary that contains the IDs of Finished Goods Line that is changed and to be
            'excluded' in calculation with the value to be used in place e.g.
            {
                'pt_1_id': {'pt_1_fg_1_id': 0.0, 'pt_1_fg_2_id': 10.0, },
                'pt_2_id': {'pt_1_fg_2_id': 5.0, },
            }
        @param recalculate_mp: A flag whether material_usage_per is to be re-calculated or not
        @returns: Nothing (True)
        '''
        select = (isinstance(ids, (int, long)) and [ids]) or ids
        select = map(lambda x: isinstance(x, dict) and x['id'] or x, select)

        _fg_pool = self.pool.get('finish.goods.line')
        for _obj in self.browse(cr, uid, select, context=context):
            _new_vals = _obj.recalc_fg_values(recalculate_mp=recalculate_mp, context=context).get(_obj.id, {})
            for _key, _vals in _new_vals.iteritems():
                if not recalculate_mp and 'material_usage_per' in _vals:
                    del _vals['material_usage_per']
                _fg_pool.write(cr, uid, [_key], _vals, context=context)
        return True

    def create_picking(self, cr, uid, ids, picking_type='internal', context=None):
        """
        This method will create the stock picking of the Product Transformation
        ---------------------------------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param ids: Identifier(s) of the current record(s)
        @param type: The type of Stock Picking to be created
        @param context: Standard Dictionary
        @returns the created Stock Picking ID
        """
        res = {}
        select = (isinstance(ids, (int, long)) and [ids]) or ids
        select = map(lambda x: isinstance(x, dict) and x['id'] or x, select)

        _sp_pool = self.pool.get('stock.picking')
        for _obj in self.browse(cr, uid, select, context=context):
            vals = {
                'origin': _obj.name,
                'date': _obj.date,
                'stock_journal_id': _obj.stock_journal_id and _obj.stock_journal_id.id or False,
                'type': picking_type,
            }
            res.update({_obj.id: _sp_pool.create(cr, uid, vals, context=context)})

        return res

    def trans_consume(self, cr, uid, ids, context=None):
        """
        This method consumes the products which are in the products to consume list and adds them in the consumed products
        and create a moves for this products.
        It also sends the state of the transformation to Consumption and sent the moves in done state.
        -------------------------------------------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param ids: Identifier(s) of the current record(s)
        @param context: Standard Dictionary
        @return True
        """
        _sp_pool = self.pool.get('stock.picking')
        wf_service = netsvc.LocalService('workflow')

        select = (isinstance(ids, (int, long)) and [ids]) or ids
        select = map(lambda x: isinstance(x, dict) and x['id'] or x, select)

        for _obj in self.browse(cr, uid, select, context=context):
            # 1. Create stock picking
            picking_id = _obj.create_picking(picking_type='internal', context=context).get(_obj.id, False)

            # 2. For each Finished Goods Line, create a stock move
            for _line in _obj.consume_line_ids:
                _line.create_move_line(picking_id, context=context)

            # 3. Bring the Stock Picking to Done state
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
            _sp_pool.force_assign(cr, uid, [picking_id], context)
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_done', cr)

            # 4. Update the Usage Cost but not the Material Percentage Use
            _obj.update_fg_values(recalculate_mp=False)

            # 5. Mark the Product Transformation as Done
            _obj.write({'state': 'consumption'}, context=context)
        return True

    _defaults = {
        'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'product.transformation'),
        'state': lambda * a: 'draft',
        'date': fields.date.context_today,
        'responsible_id': lambda self, cr, uid, ctx: uid,
        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
    }

    def trans_ready(self, cr, uid, ids, context=None):
        """
        This method checks the finished goods and if there are missing fields, it acknowledges the users regarding the same.
        """
        for _obj in self.browse(cr, uid, ids, context=context):
            for _line in _obj.finish_goods_line_ids:
                if not _line._check_ready(context=context):
                    error_str = _('Please assign a lot in the finished goods line for product: %s') % (_line.product_id.name)
                    raise osv.except_osv(_('User Error!'), error_str)
        self.write(cr, uid, ids, {'state': 'ready'}, context=context)
        return True

    def trans_done(self, cr, uid, ids, context=None):
        """
        This method finish the products which are in the finish goods product list and create moves for this finish products.
        It also sent the moves in done state.
        -------------------------------------------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param ids: Identifier(s) of the current record(s)
        @param context: Standard Dictionary
        @return True
        """
        _sp_pool = self.pool.get('stock.picking')
        wf_service = netsvc.LocalService('workflow')

        select = (isinstance(ids, (int, long)) and [ids]) or ids
        select = map(lambda x: isinstance(x, dict) and x['id'] or x, select)

        for _obj in self.browse(cr, uid, select, context=context):
            # 0. Validate that the total amount and percentage of all Finished Goods are within tolerance
            # Note that since the write has been moved up, the validation should be able to be dropped as it is done through the _constraint
            if _obj.finish_goods_line_ids:
                if float_compare(_obj.total_finish_cost, _obj.total_cost, precision_rounding=0.005):
                    raise osv.except_osv(_('Error'), _('The sum of Cost Amount of all Finished Goods Lines must be equal to the Total Finish Cost of the Product Transformation.'))
                if float_compare(_obj.total_material_usage_per, 100.0, precision_rounding=0.005):
                    raise osv.except_osv(_('Error'), _('The sum of Material Usage Percentage of all Finished Goods Lines must be equal to 100.'))

            # 1. Mark the Product Transformation as Done
            _obj.write({'state': 'done'}, context=context)

            # 2. Create stock picking
            picking_id = _obj.create_picking(picking_type='in', context=context).get(_obj.id, False)

            # 3. For each Finished Goods Line, create a stock move
            for _line in _obj.finish_goods_line_ids:
                _line.create_move_line(picking_id, context=context)

            # 4. Bring the Stock Picking to Done state
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
            _sp_pool.force_assign(cr, uid, [picking_id], context)
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_done', cr)
        return True

    def unlink(self, cr, uid, ids, context=None):
        """
        Overridden unlink method to delete a record which is in cancel state.
        ---------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param ids: Identifier of the list of records.
        @param context: Standard Dictionary
        """
        for record in self.browse(cr, uid, ids, context=context):
            if record.state != 'cancel':
                raise osv.except_osv(_('Error'), _('Only cancelled Product Transformation can be deleted.'))
        return super(product_transformation, self).unlink(cr, uid, ids, context=context)

product_transformation()


class product_consume_line(osv.osv):
    _name = 'product.consume.line'
    _description = 'Product Consume Line'
    _rec_name = 'product_id'

    def onchange_product_id(self, cr, uid, ids, product_id=False, product_uom_id=False, prodlot_id=False):
        """
        Set the product related fields when you select a product
        ----------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param ids: Current Records
        @param product_id: The Product's identifier which is selected.
        @return: A Dictionary which has key as value and a dictionary of field and values as value.
        """
        res = {'value': {}}
        product = product_id and self.pool.get('product.product').browse(cr, uid, product_id) or False
        if product:
            res['value'].update({
                'cost_method': product.cost_method,
                'product_uom_id': product_uom_id or product.uom_po_id and product.uom_po_id.id or False,
                'is_lot_based': product.is_lot_based,
                'is_auto_assign': product.is_auto_assign,
            })

            # If the Production Lot does not belong to the Product, set it to False
            _spl = prodlot_id and self.pool.get('stock.production.lot').browse(cr, uid, prodlot_id) or False
            if not _spl or (_spl.product_id.id != product_id):
                res['value'].update({'prodlot_id': False})

            res['domain'] = {'product_uom_id': [('category_id', '=', product.uom_po_id.category_id.id)]}
        else:
            res['value'].update({
                'cost_method': '',
                'product_uom_id': product_uom_id or False,
                'is_lot_based': False,
                'is_auto_assign': False,
            })
            res['domain'] = {'product_uom_id': []}

        return res

    def check_avail_stock_lot(self, cr, uid, ids, trans_id, product_id, uom_id, location_id, prodlot_id, product_qty, context=None):
        '''
        Validate whether there is sufficient stock is available in the specified Location/Production Lot
        --------------------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param product_id: The Product ID to check
        @param uom_id: The Product UoM to check
        @param location_id: The Location ID to check
        @param prodlot_id: The Production Lot ID to check
        @param product_qty: The Quantity to check
        '''
        res = {'warning': {}}
        if product_id and uom_id and prodlot_id:
            _pt = trans_id and self.pool.get('product.transformation').browse(cr, uid, trans_id, context=context) or False
            _exclude = _pt and _pt._get_to_consume_by_lot(xcld_line=[prodlot_id], context=context).get(_pt.id, {}) or {}

            # Get the available lots
            _lot_ids = self._get_lot(cr, uid,
                                     product_id,
                                     uom_id,
                                     location_ids=[location_id],
                                     required_qty=product_qty,
                                     lot_ids=[prodlot_id],
                                     exclude_lots=_exclude,
                                     raise_exception=False,
                                     context=context)

            if not _lot_ids:
                res['warning'].update({
                    'title': _('Warning!!!'),
                    'message': _('There is not enough stock in the selected Production Lots to fulfill the requested quantity!')
                })
        return res

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
        'prod_trans2_id': fields.many2one('product.transformation', 'Product Transformation'),
        'product_id': fields.many2one('product.product', 'Product', required=True, domain=[('type', '<>', 'service')]),
        'product_qty': fields.float('Qty', digits_compute=dp.get_precision('Product UoM'), required=True,),
        'product_uom_id': fields.many2one('product.uom', 'UoM ', required=True),
        'raw_loc_id': fields.many2one('stock.location', 'Raw Material Loc.'),
        'prodlot_id': fields.many2one('stock.production.lot', 'Lot #'),
        'consume_date': fields.date('Date', required=True),
        'cost_method': fields.related('product_id', 'cost_method', string='Cost Method', type='char'),
        'is_loc_selected': fields.function(_is_loc_selected, 'Is Location Selected ?', type='boolean'),
        'stock_move_id': fields.many2one('stock.move', 'Stock Move', readonly=True, help="Link to the automatically generated Stock Move."),
        'is_lot_based': fields.related('product_id', 'is_lot_based', type='boolean', string='Product Is Lot Based? '),
        'is_auto_assign': fields.related('product_id', 'is_auto_assign', type='boolean', string='Product Is Auto Assign?'),
    }

    _defaults = {
        'product_qty': lambda *a: 1.0,
        'is_loc_selected': lambda c, u, i, ctx={}: ctx.get('location_selected', False),
        'is_lot_based': lambda *a: False,
        'is_auto_assign': lambda *a: False,
    }

    def _get_lot(self, cr, uid, product_id, uom_id, location_ids=[], required_qty=0.0, lot_ids=[], exclude_lots={}, raise_exception=True, context=None):
        '''
        Get the lots that will be used to create product.consume.line and raise exception if there is
        no sufficient stock is available in the specified Location/Production Lot
        --------------------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param product_id: The Product ID to check
        @param uom_id: The Product UoM to check
        @param location_ids: A list of Location IDs to check
        @param required_qty: The Quantity to check and get
        @param lot_ids: The Production Lot IDs to check
        @param exclude_lots: A dictionary that contains the Production Lot IDs and quantities to
               exclude from checking, e.g. if used by other product.consume.line in the same
               product transformation
        @param raise_exception: Whether or not to raise exception if stock is not available
        '''
        if not context:
            context = {}

        rv = []
        _prd_pool = self.pool.get('product.product')
        _prd_obj = product_id and _prd_pool.browse(cr, uid, product_id, context=context) or False
        if not _prd_obj:
            if raise_exception:
                raise osv.except_osv(_('No Product Specified!'), _('Incorrect or no product is specified for stock checking!!!!'))
            else:
                return rv

        # Get the lots to be assigned
        _spl_pool = self.pool.get('stock.production.lot')
        cost_method = _prd_obj and _prd_obj.cost_method or ''
        if _prd_obj.is_auto_assign or (_prd_obj.is_lot_based and not lot_ids):
            # For lot based products that is to be auto assigned (no lots assigned or auto assign cost method)
            order_by = 'date%s' % ((cost_method == 'lifo') and ' DESC' or '')
            _lot_ids = _spl_pool.search(cr, uid, [('product_id', '=', product_id), ('stock_available', '>', 0)], order=order_by)
        else:
            # For non-auto assigned lot based products that has lots assigned already
            _lot_ids = lot_ids

        # Convert the required quantity to Product's default UOM
        _uom_pool = self.pool.get('product.uom')
        if uom_id != (_prd_obj.uom_id and _prd_obj.uom_id.id or False):
            _uom = _uom_pool.browse(cr, uid, uom_id, context=context)
            _base_req_qty = _uom_pool._compute_qty_obj(cr, uid, _uom, required_qty, _prd_obj.uom_id, context=context)
        else:
            _base_req_qty = required_qty

        # Check whether there is enough stock available
        available_qty = 0.0
        for lot in _spl_pool.browse(cr, uid, _lot_ids, context=context):
            if lot.product_id.id != product_id:
                raise osv.except_osv(_('Incorrect Lot!'), _('Selected Production Lot %s does not contain Product %s!') % (lot.name, _prd_obj.name_template))

            _ctx = context.copy()
            _ctx.update({
                'prodlot_id': lot.id,
                'location': location_ids,
            })
            _prd_obj = _prd_obj.browse(context=_ctx)
            _prd_obj = _prd_obj and _prd_obj[0] or False

            available_qty += _prd_obj.qty_available
            available_qty -= exclude_lots.get(lot.id, 0.0)
            rv.append(lot.id)
            if available_qty >= _base_req_qty:
                break

        # For non-lot based products, search by location
        if not _lot_ids and not _prd_obj.is_lot_based:
            _ctx = context.copy()
            _ctx.update({
                'location': location_ids,
            })
            _prd_obj = _prd_obj.browse(context=_ctx)
            _prd_obj = _prd_obj and _prd_obj[0] or False

            available_qty = _prd_obj.qty_available
            rv.append(False)

        if available_qty < _base_req_qty:
            if raise_exception:
                _qual = _('existing Production Lots')
                if lot_ids:
                    _qual = [x.name for x in _spl_pool.browse(cr, uid, lot_ids, context=context)]
                    _qual = _qual and (_('Production Lots %s') % ', '.join(_qual)) or ''
                loc_names = ''
                if location_ids:
                    _loc_pool = self.pool.get('stock.location')
                    loc_names = [x.name for x in _loc_pool.browse(cr, uid, location_ids, context=context)]
                    loc_names = loc_names and (_(' at Locations %s') % ', '.join(loc_names)) or ''
                raise osv.except_osv(_('Insufficient Stock!'), _('Only %.2f of Product %s is available while %.2f is requested in the %s%s!') % (available_qty, _prd_obj.name_template, _base_req_qty, _qual, loc_names))
            else:
                return []

        return rv

    def create(self, cr, uid, vals, context=None):
        rv = False
        _prd_id = vals.get('product_id', False)
        _pt_id = vals.get('prod_trans_id', False) or context.get('active_id', False)

        # Product ID and Product Transformation ID are required during Creation
        if not _prd_id or not _pt_id:
            raise osv.except_osv(_('User Error!'), _('Insufficient information given!'))

        _qty = vals.get('product_qty', 0.0)
        if not _qty:
            raise osv.except_osv(_('Error'), _("Product to consume is 0.00."))

        _prd_pool = self.pool.get('product.product')
        _spl_pool = self.pool.get('stock.production.lot')

        # Check whether there is enough stock available
        _prd_obj = _prd_id and _prd_pool.browse(cr, uid, _prd_id, context=context) or False
        _lot_ids = _prd_obj.is_auto_assign and vals.get('prodlot_id', False) or False
        _lot_ids = _lot_ids and [_lot_ids] or []
        required_qty = vals.get('product_qty', 0.0)
        required_uom = vals.get('product_uom_id', False)
        _ptrans_pool = self.pool.get('product.transformation')
        _pt = _pt_id and _ptrans_pool.browse(cr, uid, _pt_id, context=context) or False
        _exclude = _pt and _pt._get_to_consume_by_lot(context=context).get(_pt.id, {}) or {}

        # Values taken from parent Product Transformation
        _loc_id = vals.get('raw_loc_id', False) or (_pt and _pt.raw_src_loc_id and _pt.raw_src_loc_id.id) or False
        date = vals.get('consume_date', False) or (_pt and _pt.date) or time.strftime(DEFAULT_SERVER_DATE_FORMAT)

        if _lot_ids or _prd_obj.is_auto_assign:
            _loc_ids = _loc_id and [_loc_id] or []
            _lot_ids = self._get_lot(cr, uid, _prd_id, required_uom, location_ids=_loc_ids, required_qty=required_qty, lot_ids=_lot_ids, exclude_lots=_exclude, context=context)

        if _prd_obj.is_auto_assign:
            for lot in _spl_pool.browse(cr, uid, _lot_ids, context=context):
                if required_qty <= 0:
                    break
                lot_qty = min(required_qty, lot.stock_available)
                _update_vals = {
                    'product_qty': lot_qty,
                    'raw_loc_id': _loc_id,
                    'consume_date': date,
                    'prodlot_id': lot.id,
                }
                vals.update(_update_vals)
                rv = super(product_consume_line, self).create(cr, uid, vals, context=context)
                required_qty -= lot_qty
        elif _prd_obj.is_lot_based:
            _update_vals = {
                'raw_loc_id': _loc_id,
                'consume_date': date,
                'prodlot_id': vals.get('prodlot_id', False),
            }
            vals.update(_update_vals)
            rv = super(product_consume_line, self).create(cr, uid, vals, context=context)
        else:
            _update_vals = {
                'raw_loc_id': _loc_id,
                'consume_date': _pt.date,
                'prodlot_id': False,
            }
            vals.update(_update_vals)
            rv = super(product_consume_line, self).create(cr, uid, vals, context=context)

        return rv

    def write(self, cr, uid, ids, vals, context=None):
        _prd_pool = self.pool.get('product.product')

        for _obj in self.browse(cr, uid, ids, context=context):
            _prd_id = vals.get('product_id', _obj.product_id and _obj.product_id.id or False)
            _prd_obj = _prd_pool.browse(cr, uid, _prd_id, context=context)

            # Values taken from parent Product Transformation
            _pt = _obj.prod_trans_id
            _loc_id = vals.get('raw_loc_id', False) or (_obj.raw_loc_id and _obj.raw_loc_id.id or False) or (_pt and _pt.raw_src_loc_id and _pt.raw_src_loc_id.id or False) or False
            date = (_prd_obj.is_lot_based and _pt and _pt.date or False) or vals.get('consume_date', _obj.consume_date or _pt and _pt.date or False) or time.strftime(DEFAULT_SERVER_DATE_FORMAT)

            # Check whether there is enough stock available
            _prodlot_id = vals.get('prodlot_id', _obj.prodlot_id and _obj.prodlot_id.id or False)
            _qty = vals.get('product_qty', _obj.product_qty or 0.0)
            _lot_ids = _prodlot_id and [_prodlot_id] or []
            _uom = vals.get('product_uom_id', _obj.product_uom_id.id or False)
            _exclude = _pt and _pt._get_to_consume_by_lot(xcld_line=[_obj.id], context=context).get(_pt.id, {}) or {}
            _loc_ids = _loc_id and [_loc_id] or []
            _lot_ids = self._get_lot(cr, uid, _prd_id, _uom, location_ids=_loc_ids, required_qty=_qty, lot_ids=_lot_ids, exclude_lots=_exclude, context=context)

            _update_vals = {
                'raw_loc_id': _loc_id,
                'consume_date': date,
                'prodlot_id': _prd_obj.is_lot_based and _prodlot_id or False,
            }
            _to_write = vals.copy()
            _to_write.update(_update_vals)

            super(product_consume_line, self).write(cr, uid, [_obj.id], _to_write, context=context)

        return True

    def create_move_line(self, cr, uid, ids, picking_id, context=None):
        """
        This method will create the move line of the Finished Good Line
        ---------------------------------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param ids: Identifier(s) of the current record(s)
        @param picking_id: The Stock Picking to link the created Stock Move to.
        @param context: Standard Dictionary
        @returns a list of created Stock Move IDs
        """
        res = {}
        select = (isinstance(ids, (int, long)) and [ids]) or ids
        select = map(lambda x: isinstance(x, dict) and x['id'] or x, select)

        _sm_pool = self.pool.get('stock.move')
        for _obj in self.browse(cr, uid, select, context=context):
            _trans = _obj.prod_trans_id
            # 1. Create a stock move
            _src_loc = (_obj.raw_loc_id and _obj.raw_loc_id.id) or (_trans.raw_src_loc_id and _trans.raw_src_loc_id.id) or False
            if not _src_loc:
                raise osv.except_osv(_('Error'), _("No source location is provided for Consumed Good for Product Transformation %s or one of it's Line to Consume") % (_trans.name))

            _vals = {
                'product_id': _obj.product_id and _obj.product_id.id or False,
                'product_qty': _obj.product_qty,
                'product_uom': _obj.product_uom_id and _obj.product_uom_id.id or False,
                'prodlot_id': _obj.prodlot_id and _obj.prodlot_id.id or False,
                'date': _obj.consume_date,
                'location_id': _src_loc,
                'name': "%s %s" % (_trans.name, _obj.product_id and _obj.product_id.name or ''),
                'location_dest_id': _trans.trans_loc_id and _trans.trans_loc_id.id or False,
                'picking_id': picking_id
            }
            move_id = _sm_pool.create(cr, uid, _vals, context=context)
            res.update({_obj.id: move_id})

            # 2. Associate the record as Consumed Products of the Product Transformation
            #    Disassociate the record from Product to Consume of the Product Transformation
            #    Associate the stock move with the Consumed Product
            _obj.write({'prod_trans_id': False, 'prod_trans2_id': _trans.id, 'stock_move_id': move_id})

        return res

product_consume_line()


class finish_goods_line(osv.osv):
    _name = 'finish.goods.line'
    _description = 'Finished Goods'
    _rec_name = 'product_id'

    def onchange_product_id(self, cr, uid, ids, product_id):
        """
        Set the product default UoM when you select a product
        ----------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param ids: Current Records
        @param product_id: The Product's identifier which is selected.
        @return: A Dictionary which has key as value and a dictionary of field and values as value.
        """
        res = {}
        product = product_id and self.pool.get('product.product').browse(cr, uid, product_id) or False
        if product:
            res['value'] = {
                'product_uom_id': product.uom_id and product.uom_id.id or False,
                'cost_method': product.cost_method or '',
                'is_lot_based': product.is_lot_based,
            }
        else:
            res['value'] = {
                'product_uom_id': False,
                'cost_method': '',
                'is_lot_based': False,
            }
        return res

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
        'trans_state': fields.related('prod_trans_id', 'state', string='Transformation State', type='selection', selection=TRANS_STATES),
        'product_id': fields.many2one('product.product', 'Product', domain=[('type', '<>', 'service')]),
        'product_qty': fields.float('Qty', digits_compute=dp.get_precision('Product UoM')),
        'product_uom_id': fields.many2one('product.uom', 'UoM'),
        'finish_goood_loc_id': fields.many2one('stock.location', 'Finished Goods Loc'),
        'prodlot_id': fields.many2one('stock.production.lot', 'Lot #'),
        'date': fields.date('Date'),
        'material_usage_per': fields.float('Material Usage %', digits_compute=dp.get_precision('Purchase Price')),
        'cost_amount': fields.float('Cost Amount', required=True, digits_compute=dp.get_precision('Purchase Price')),
        'cost_method': fields.related('product_id', 'cost_method', string='Cost Method', type='char'),
        'is_loc_selected': fields.function(_is_loc_selected, 'Is Location Selected ?', type='boolean'),
        'stock_move_id': fields.many2one('stock.move', 'Stock Move', readonly=True, help="Link to the automatically generated Stock Move."),
        'is_lot_based': fields.related('product_id', 'is_lot_based', type='boolean', string='Product Is Lot Based? '),
    }

    _defaults = {
        'cost_amount': 0.0,
        'date': fields.date.context_today,
        'product_qty': lambda *a: 1.0,
        'is_loc_selected': lambda c, u, i, ctx={}: ctx.get('location_selected', False),
        'is_lot_based': lambda *a: False,
    }

    def _check_ready(self, cr, uid, ids, context=None):
        """
        This method checks that necessary information are available
        """
        select = (isinstance(ids, (int, long)) and [ids]) or ids
        select = map(lambda x: isinstance(x, dict) and x['id'] or x, select)

        rv = True
        for _obj in self.browse(cr, uid, select, context=context):
                _product = _obj.product_id
                if _product:
                    _line_ready = True
                    if _product.is_lot_based:
                        _line_ready = _obj.prodlot_id or False
                    rv = rv and _line_ready
        return rv

    def create(self, cr, uid, vals, context=None):
        '''
        Set the Material Usage % and Cost Amount on the basis of Product quantity and total quantity
        --------------------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param vals: Current Record Dictionary
        @return: ID of created record
        '''
        _obj_id = super(finish_goods_line, self).create(cr, uid, vals, context=context)
        _obj = self.browse(cr, uid, _obj_id, context=context)
        _obj.prod_trans_id.update_fg_values(recalculate_mp=context.get('recalculate_mp', True), context=context)
        return _obj_id

    def write(self, cr, uid, ids, vals, context=None):
        '''
        Set the Material Usage % and Cost Amount on the basis of Product quantity and total quantity
        --------------------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param id: Current Record ID
        @param vals: Current Record Dictionary
        '''
        select = (isinstance(ids, (int, long)) and [ids]) or ids
        select = map(lambda x: isinstance(x, dict) and x['id'] or x, select)

        if 'product_qty' not in vals:
            return super(finish_goods_line, self).write(cr, uid, select, vals, context=context)
        else:
            # Construct the modified lines dictionary
            _mod_lines = {}
            _new_qty = vals.get('product_qty', 0.0)
            for _obj in self.browse(cr, uid, select, context=context):
                _mod_lines.setdefault(_obj.prod_trans_id.id, {}).update({_obj.id: _new_qty})

            # Calculate the updated Material Usage Percentage and Cost Amount for each affected Product Transformation
            # Material Usage Percentage is recalculated if not specified in any of the lines
            _trans_ids = _mod_lines.keys()
            _val_by_trans = self.pool.get('product.transformation').recalc_fg_values(cr, uid, _trans_ids, mod_lines=_mod_lines, recalculate_mp=False, context=context)
            _val_update = {}
            for _val in _val_by_trans.itervalues():
                _val_update.update(_val)

            # Do the actual update to the augmented list of IDs
            for _line_id, _val in _val_update.iteritems():
                # If _line_id belongs to the original select, add the vals to _val
                if _line_id in select:
                    _val.update(vals)
                    select.remove(_line_id)
                super(finish_goods_line, self).write(cr, uid, [_line_id], _val, context=context)
            if select:
                super(finish_goods_line, self).write(cr, uid, select, vals, context=context)
        return True

    def unlink(self, cr, uid, ids, context=None):
        '''
        Delete the record and update the Material Usage Percentage and Cost Amount of every Finished
        Good Lines related to every affected Produt Transformation
        --------------------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param id: Current Record ID
        '''
        select = (isinstance(ids, (int, long)) and [ids]) or ids
        select = map(lambda x: isinstance(x, dict) and x['id'] or x, select)
        _todo = [_obj.prod_trans_id.id for _obj in self.browse(cr, uid, select, context=context)]
        rv = super(finish_goods_line, self).unlink(cr, uid, select, context=context)

        # Update the Material Usage Percentage and Cost Amount
        _todo = list(set(_todo))
        for _trans in self.pool.get('product.transformation').browse(cr, uid, _todo, context=context):
            _trans.update_fg_values(recalculate_mp=True, context=context)

        return rv

    def onchange_product_qty(self, cr, uid, ids, product_qty, original_mp, trans_id, context=None):
        """
        When you change quantity in the finish goods line, this method updates the cost amount and material usage.
        ----------------------------------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in user
        @param ids: Identifiers of the current records
        @param product_qty: Product Qty that is changed
        @param trans_id: ID of the parent Product Transformation
        @param context: Standard Dictionary
        @return A Dictionary that contains 'value' as key and field,value dictionary as value
        """
        res = {}
        _trans = trans_id and self.pool.get('product.transformation').browse(cr, uid, trans_id, context=context) or False
        if not _trans or not ids or not _trans.total_cost:
            return res

        total_qty = _trans._get_fg_qty_total(exclude_ids=ids, context=context).get(_trans.id)
        # Add product_qty times the number of excluded IDs, ids usually only contain 1 member
        total_qty += (product_qty * len(ids))

        res['value'] = calc_usage(cr, qty=product_qty, total_qty=total_qty, total_cost=_trans.total_cost, recalculate_mp=False, original_mp=original_mp)
        return res

    def onchange_material_per(self, cr, uid, ids, material_usage, product_qty, total_cost):
        """
        When you change the material percentage it changes the cost amount of the particular finished goods line.
        ---------------------------------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param ids: Identifier(s) of the current record(s)
        @param material_usage: material usage that is changed
        @param total_cost: Total cost of the transformation
        @return A Dictionary that contains 'value' as key and field,value dictionary as value
        """
        res = {}
        rv = calc_usage(cr, qty=product_qty, total_cost=total_cost, recalculate_mp=False, original_mp=material_usage)
        for k in rv.keys():
            if k not in ['cost_amount']:
                del rv[k]
        res['value'] = rv
        return res

    def compute_usage_cost_amount(self, cr, uid, transformation, recalculate_mp=True, context=None):
        """
        This method is here for backward compatibility as via_lot_valuation uses this.  It should be refactored
        together with via_lot_valuation
        """
        transformation.update_fg_values(recalculate_mp=recalculate_mp, context=context)
        return True

    def onchange_cost_amount(self, cr, uid, ids, cost_amount, total_cost):
        """
        When you change the cost_amount it changes the material usage percentage of the particular finished goods line.
        ---------------------------------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param ids: Identifier(s) of the current record(s)
        @param cost_amount: Cost amount which is changed
        @param total_cost: Total cost of the transformation
        @return A Dictionary that contains 'value' as key and field,value dictionary as value
        """
        res = {}
        rv = calc_usage(cr, total_cost=total_cost, cost_amount=cost_amount, reverse_calc=True)
        for k in rv.keys():
            if k not in ['material_usage_per']:
                del rv[k]
        res['value'] = rv
        return res

    def create_move_line(self, cr, uid, ids, picking_id, context=None):
        """
        This method will create the move line of the Finished Good Line
        ---------------------------------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param ids: Identifier(s) of the current record(s)
        @param picking_id: The Stock Picking to link the created Stock Move to.
        @param context: Standard Dictionary
        @returns a list of created Stock Move IDs
        """
        if not context:
            context = {}

        res = {}
        select = (isinstance(ids, (int, long)) and [ids]) or ids
        select = map(lambda x: isinstance(x, dict) and x['id'] or x, select)

        _sm_pool = self.pool.get('stock.move')
        _uom_pool = self.pool.get('product.uom')
        for _obj in self.browse(cr, uid, select, context=context):
            _trans = _obj.prod_trans_id
            # 1. Create a stock move
            _dest_loc = (_obj.finish_goood_loc_id and _obj.finish_goood_loc_id.id) or (_trans.finish_goods_loc_id and _trans.finish_goods_loc_id.id) or False
            if not _dest_loc:
                raise osv.except_osv(_('Error'), _("No destination location is provided for Finsihed Good for Product Transformation %s or one of it's Finsihed Good Lines") % (_trans.name))

            _vals = {
                'product_id': _obj.product_id and _obj.product_id.id or False,
                'product_qty': _obj.product_qty,
                'product_uom': _obj.product_uom_id and _obj.product_uom_id.id or False,
                'prodlot_id': _obj.prodlot_id and _obj.prodlot_id.id or False,
                'date': _obj.date,
                'location_id': _trans.trans_loc_id and _trans.trans_loc_id.id or False,
                'name': "%s %s" % (_trans.name, _obj.product_id and _obj.product_id.name or ''),
                'location_dest_id': _dest_loc,
                'picking_id': picking_id,
            }
            move_id = _sm_pool.create(cr, uid, _vals, context=context)
            res.update({_obj.id: move_id})

            # 2. Associate the stock move with the Finished Goods Line
            _obj.write({'stock_move_id': move_id})

            # 3. Update the related Lot ID's Cost Price Per Unit and Product's Standard Price
            _sm = _sm_pool.browse(cr, uid, move_id, context=context)
            _price = _obj.cost_amount / _obj.product_qty
            _product = _sm.product_id

            if _product.cost_method in LOT_BASED_METHODS + ['average']:
                # This portion is taken from the average price computation section of do_partial method
                # of stock.picking or stock.move.  May need refactoring when those methods are revised.
                _prod_uom_id = _sm.product_id and _sm.product_id.uom_id and _sm.product_id.uom_id.id or False
                _sm_uom_id = _sm.product_uom and _sm.product_uom.id or False
                _ccy_id = _sm.company_id and _sm.company_id.currency_id and _sm.company_id.currency_id.id or False
                qty = _uom_pool._compute_qty(cr, uid, _sm_uom_id, _sm.product_qty, _prod_uom_id)
                if qty > 0:
                    new_price = _uom_pool._compute_price(cr, uid, _sm_uom_id, _price, _prod_uom_id)
                    # Set the new price for the standard price, this will be used if there is currently no (or negative) stock
                    new_std_price = new_price
                    if _product.qty_available > 0:
                        # Re-calculate the average price based
                        _ctx = context.copy()
                        _ctx.update({'currency_id': _ccy_id})
                        amount_unit = _product.price_get('standard_price', context=_ctx)[_product.id]
                        new_std_price = ((amount_unit * _product.qty_available) + (new_price * qty))/(_product.qty_available + qty)

                    _product.write({'standard_price': new_std_price})

                    # Record the values, so they can be used for inventory valuation if real-time valuation is enabled.
                    _sm.write({'price_unit': _price, 'price_currency_id': _ccy_id, })
                if _product.cost_method in LOT_BASED_METHODS:
                    _sm.prodlot_id.write({'cost_price_per_unit': _price}, context=context)
            else:
                _product.write({'standard_price': _price}, context=context)

        return res

finish_goods_line()

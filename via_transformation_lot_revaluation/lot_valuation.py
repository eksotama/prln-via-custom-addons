# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Infinity  PT. Vikasa Infinity Anugrah (<http://www.infi-nity.com>) 
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
#############################################################################
from osv import osv,fields
import time
from tools import DEFAULT_SERVER_DATE_FORMAT
import netsvc

class lot_valuation(osv.osv):
    
    _inherit = 'lot.valuation'
    
    def valuation_done(self, cr, uid, ids, context=None):
        """
        This method revaluates the transformed finished goods from the consumed prodct.
        @param self : object pointer
        @param cr : database cursor
        @param ids : identifier(s) of the current record(s)
        @param context : standard dictionary
        @return True
        """
        trans_obj = self.pool.get('product.transformation')
        acc_mov_obj = self.pool.get('account.move')
        acc_mov_line_obj = self.pool.get('account.move.line')
        prod_cons_obj = self.pool.get('product.consume.line')
        finish_goods_obj = self.pool.get('finish.goods.line') 
        user_obj = self.pool.get('res.users')
        valuation_obj = self.pool.get('lot.valuation')
        res = super(lot_valuation,self).valuation_done(cr, uid, ids, context=context)
        wf_service = netsvc.LocalService('workflow')
        for valuation in self.browse(cr, uid, ids, context=context):
            #Get the consumed products in the transformation
            val_dif = valuation.valuation_cost_price - valuation.existing_cost_price
            cons_ids = prod_cons_obj.search(cr, uid, [('prodlot_id','=',valuation.lot_id.id),('prod_trans2_id', '!=', False)], context=context)
            for cons_line in prod_cons_obj.browse(cr, uid, cons_ids, context=context):
                #Get the transformation related to the consumed product
                transformation = cons_line.prod_trans2_id
                if transformation.state in ('consumption','ready'):
                    #If product already consumed but not processed just update the finished goods cost_amount 
                    finish_goods_obj.compute_usage_cost_amount(cr, uid, transformation, context=context)
                elif transformation.state == 'done':
                    #If the product transformation has already been processed and finished.
                    #Get the old cost_amount and generate the new amount and create moves for the diff between them.
                    trans_out_acc = transformation.trans_loc_id.valuation_out_account_id.id
                    finish_goods_in_acc = transformation.trans_loc_id.valuation_in_account_id.id
                    valuation_journal_id = user_obj.browse(cr, uid, uid, context=context).company_id.valuation_journal_id.id
                    for line in transformation.finish_goods_line_ids:
                        cost_amount = (line.material_usage_per * transformation.total_cost)/100
                        diff = cost_amount - line.cost_amount
                        finish_goods_obj.write(cr, uid, [line.id], {'cost_amount' : cost_amount}, context=context)
                        if diff != 0.0:
                            if line.product_id.cost_method in ('fifo', 'lifo', 'lot_based'):
                                cost_price = line.cost_amount/line.product_qty
                            else:
                                cost_price = line.product_id.standard_price
                            val_dict = {
                                'product_id' : line.product_id.id,
                                'lot_id' : line.prodlot_id.id,
                                'date' : time.strftime(DEFAULT_SERVER_DATE_FORMAT),
                                'product_uom_id' : line.product_id.uom_id,
                                'existing_cost_price' : cost_price,
                                'valuation_cost_price' : abs(cost_amount) / line.product_qty
                            }
                            valuation_id = valuation_obj.create(cr, uid, val_dict, context=context)
                            wf_service.trg_validate(uid, 'lot.valuation', valuation_id, 'schedule', cr)
                            wf_service.trg_validate(uid, 'lot.valuation', valuation_id, 'done', cr)
        return res
    
lot_valuation()
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

from osv import osv
import netsvc
from tools.translate import _


class product_transformations_wizard(osv.osv_memory):
    _name = 'product.transformations.wizard'

    def process(self, cr, uid, ids, context=None):
        ids = context.get('active_ids', [])
        wf_service = netsvc.LocalService('workflow')
        state_filter = context.get('process')
        signal = "action_%s" % (state_filter)
        for trans in self.pool.get('product.transformation').browse(cr, uid, ids, context=context):
            if (state_filter == 'consume') and (trans.state in ['draft', 'consumption']):
                if len(trans.consume_line_ids):
                    wf_service.trg_validate(uid, 'product.transformation', trans.id, signal, cr)
                else:
                    error_str = _('Please assign product(s) to consume for product transformation %s') % (trans.name)
                    raise osv.except_osv(_('Nothing to Process!'), error_str)
            elif (state_filter == 'ready') and (trans.state in ['consumption']):
                if len(trans.finish_goods_line_ids):
                    wf_service.trg_validate(uid, 'product.transformation', trans.id, signal, cr)
                else:
                    error_str = _('Please assign finish good line(s) to process for product transformation %s') % (trans.name)
                    raise osv.except_osv(_('Nothing to Process!'), error_str)
            elif (state_filter == 'done') and (trans.state in ['ready']):
                wf_service.trg_validate(uid, 'product.transformation', trans.id, signal, cr)
            else:
                pass
        return {'type': 'ir.actions.act_window_close'}

product_transformations_wizard()

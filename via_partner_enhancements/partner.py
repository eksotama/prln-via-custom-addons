# -*- encoding: utf-8 -*-
##############################################################################
#
#    Vikasa Infinity Anugrah, PT
#    Copyright (c) 2011 - 2012 Vikasa Infinity Anugrah <http://www.infi-nity.com>
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
from osv import fields

from tools.translate import _

class res_partner(osv.osv):
    _inherit = 'res.partner'

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        if not args:
            args = []
        args = args[:]

        _name_filter = False
        pos = 0
        while pos < len(args):
            if args[pos][0] == 'name' and args[pos][2]:
                _name_filter = args[pos][2]
                break
            pos += 1

        if _name_filter:
            args.insert(pos, ('partner_info.value', 'ilike', _name_filter))
            args.insert(pos, '|')

        return super(res_partner, self).search(cr, uid, args, offset, limit,
                order, context=context, count=count)

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not context:
            context={}
        if not args:
            args = []
        args = args[:]

        if name:
            ids = self.search(cr, uid, [('ref', '=', name)] + args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, uid, [('partner_info.value', 'ilike', name)] + args, limit=limit, context=context)
                if not ids:
                    ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

#    def _partner_tree_search(self, cursor, user, ids, name, arg, context=None):
#        res = {}
#        for partner in self.browse(cursor, user, ids, context=context):
#	    result = ''
#            for info in partner.partner_info:
##                if invoice.state not in ('draft','cancel'):
##                    tot += invoice.amount_untaxed
#            	if info.partner_parameter:
##                    res[partner.id] = info['partner_parameter'] + ' = ' + info['value'] + ' | '
##              	     res[partner.id] = info['value']
#		    result = info['value']
##            else:
##                res[purchase.id] = 0.0
#	    res[partner.id] = result
#        return res

    _columns = {
        'partner_info': fields.one2many('partner.info', 'partner_id', 'Partner Info'),
    }

res_partner()

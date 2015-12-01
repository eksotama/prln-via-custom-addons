# -*- encoding: utf-8 -*-
##############################################################################
#
#    Vikasa Infinity Anugrah, PT
#    Copyright (c) 2011 - 2014 Vikasa Infinity Anugrah <http://www.infi-nity.com>
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


class account_asset_depreciation_line(osv.osv):
    _inherit = 'account.asset.depreciation.line'

    def create_move(self, cr, uid, ids, context=None):
        created_move_ids = super(account_asset_depreciation_line, self).create_move(cr, uid, ids, context=context)
        for line in self.browse(cr, uid, ids, context=context):
            if line.move_id.id in created_move_ids:
                depreciation_date = line.depreciation_date or fields.date.context_today
                line.move_id.write({'date': depreciation_date}, context=context)
                for move_line in line.move_id.line_id:
                    move_line.write({'date': depreciation_date}, context=context)
        return created_move_ids

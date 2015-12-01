# -*- encoding: utf-8 -*-
##############################################################################
#
#    Vikasa Infinity Anugrah, PT
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
from tools.translate import _


class account_move_line(osv.osv):
    _inherit = 'account.move.line'

    def _get_signed_amount_residual(self, cr, uid, ids, field_names, args, context=None):
        """
           A adapted copy if the _amount_residual method in account/account_move_line.py allowing
           calculation of residual amount in company currency to any account type based on
           reconciliation
        """
        res = {}
        if context is None:
            context = {}

        for move_line in self.browse(cr, uid, ids, context=context):
            if move_line.reconcile_id:
                continue
            line_total_in_company_currency = move_line.debit - move_line.credit
            if move_line.reconcile_partial_id:
                for payment_line in move_line.reconcile_partial_id.line_partial_ids:
                    if payment_line.id == move_line.id:
                        continue
                    line_total_in_company_currency += (payment_line.debit - payment_line.credit)

            res[move_line.id] = line_total_in_company_currency
        return res

    _columns = {
        'signed_amount_residual': fields.function(_get_signed_amount_residual, method=True, string='Available Amount', type='float', readonly=True),
    }

account_move_line()


class account_move(osv.osv):
    _inherit = 'account.move'

    def validate(self, cr, uid, ids, context=None):
        # Add a validation process that all periods being posted is still open
        for _obj in self.browse(cr, uid, ids, context=context):
            if _obj.period_id.state in ('done'):
                raise osv.except_osv(_('Error!'), _("Move %s is dated in closed period.") % (_obj.name))

        return super(account_move, self).validate(cr, uid, ids, context=context)

account_move()

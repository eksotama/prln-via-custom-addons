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

from osv import fields, osv
from datetime import date


class wizard_tax_realisation(osv.osv_memory):
    _name = 'account.wizard_tax_realisation'
    _descripton = 'Wizard Tax Realisation'

    _columns = {
        'realisation_date': fields.date(string='Realisation Date', required=True),
    }

    _defaults = {
        'realisation_date': lambda *a: date.today().strftime('%Y-%m-%d'),
    }

    def realise_tax(self, cr, uid, ids, context=None):
        if not context:
            context = {}

        # It is assumed that only 1 wizard is valid at any time
        obj_wizard = self.pool.get('account.wizard_tax_realisation')
        wizard = ids and obj_wizard.browse(cr, uid, ids[0], context=context) or False
        _date = wizard and wizard.realisation_date or date.today().strftime('%Y-%m-%d')
        self.pool.get('account.invoice.tax').realise_tax(cr, uid, context.get('active_ids', []), _date)

        return {'type': 'ir.actions.act_window_close'}

wizard_tax_realisation()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

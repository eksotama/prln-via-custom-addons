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
from tools.translate import _


class wizard_create_taxform_realisation(osv.osv_memory):
    _name = 'account.wizard_create_taxform_realisation'

    def default_invoice_realised(self, cr, uid, context=None):
        _inv_tax = self.pool.get('account.invoice.tax').browse(cr, uid, context['active_id'], context=context)

        return _inv_tax.realise_move_id and True or False

    def default_create_realisation(self, cr, uid, context=None):
        _inv_tax = self.pool.get('account.invoice.tax').browse(cr, uid, context['active_id'], context=context)

        return not (_inv_tax.realise_move_id and True or False)

    _columns = {
        'invoice_realised': fields.boolean(string='Invoice Realised'),
        'create_realisation': fields.boolean(string='Create Realisation Entry'),
        'realisation_date': fields.date(string='Realisation Date'),
    }

    _defaults = {
        'invoice_realised': default_invoice_realised,
        'create_realisation': default_create_realisation,
        'realisation_date': lambda *a: date.today().strftime('%Y-%m-%d'),
    }

    def create_taxform(self, cr, uid, ids, context=None):
        if not context:
            context = {}

        # It is assumed that only 1 wizard is valid at any time
        obj_wizard = self.pool.get('account.wizard_create_taxform_realisation')
        wizard = ids and obj_wizard.browse(cr, uid, ids[0], context=context) or False
        _date = wizard and wizard.realisation_date or date.today().strftime('%Y-%m-%d')

        _realise = wizard and wizard.create_realisation or False
        if _realise:
            self.pool.get('account.invoice.tax').realise_tax(cr, uid, context.get('active_ids', []), _date, context=context)

        self.pool.get('account.invoice.tax').create_taxform(cr, uid, context.get('active_ids', []), context=context)

        return {'type': 'ir.actions.act_window_close'}

wizard_create_taxform_realisation()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

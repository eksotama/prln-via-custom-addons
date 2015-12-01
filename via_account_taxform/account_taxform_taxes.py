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

import netsvc
from osv import fields, osv
import decimal_precision as dp


class account_taxform_taxes(osv.osv):
    _name = "account.taxform.taxes"
    _description = "Taxes related to a taxform"
    logger = netsvc.Logger()

    def _get_tax_category(self, cr, uid, context=None):
        res = self.pool.get('code.decode').get_company_selection_for_category(cr, uid, 'via_account_taxform', 'tax_category', context=context)
        return res

    _columns = {
        'taxform_id': fields.many2one('account.taxform', 'Taxform Id'),
        'invoice_id': fields.related('taxform_id', 'invoice_id', type="many2one", relation='account.invoice', store=True, string='Invoice'),
        'tax_cat': fields.selection(_get_tax_category, 'Tax Category'),
        'tax_id': fields.many2one('account.tax', 'Tax Id', store=True),
        'tariff': fields.related('tax_id', 'amount', type='float', string='Tariff', store=True, select=True),
        'tax_base': fields.float('Tax Base Amount', digits_compute=dp.get_precision('Account')),
        'amount_tax': fields.float('Tax Amount', digits_compute=dp.get_precision('Account'))
    }

account_taxform_taxes()

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
from via_base_enhancements.tools import prep_dict_for_write


class account_invoice(osv.osv):
    _inherit = 'account.invoice'

    def _refund_cleanup_lines(self, cr, uid, lines):
        rv = super(account_invoice, self)._refund_cleanup_lines(cr, uid, lines)

        for line in rv:
            for field in ['realise_move_id']:
                if line[2].get(field):
                    del line[2][field]
        return rv

account_invoice()


class account_invoice_tax(osv.osv):
    _inherit = 'account.invoice.tax'

    _columns = {
        'realise_move_id': fields.many2one(string='Realisation Entry', obj='account.move'),
    }

    def get_realisation_journal(self, cr, uid, ids, context=None):
        res = {}
        if not context:
            context = {}
        select = ids
        if isinstance(select, (int, long, )):
            select = [ids]

        for _tax in self.pool.get('account.invoice.tax').browse(cr, uid, select, context=context):
            res[_tax.id] = False
            _invoice_type = _tax.invoice_id.type
            _account = _tax.account_id
            if _invoice_type in ('in_invoice', 'out_invoice'):
                res[_tax.id] = _account.invoice_realisation_journal_id
            elif _invoice_type in ('in_refund', 'out_refund'):
                res[_tax.id] = _account.refund_realisation_journal_id

        return isinstance(ids, (int, long, )) and res[ids] or res

    def get_realisation_account(self, cr, uid, ids, context=None):
        res = {}
        if not context:
            context = {}
        select = ids
        if isinstance(select, (int, long, )):
            select = [ids]

        for _tax in self.pool.get('account.invoice.tax').browse(cr, uid, select, context=context):
            res[_tax.id] = False
            _invoice_type = _tax.invoice_id.type
            _account = _tax.account_id
            if _invoice_type in ('in_invoice', 'out_invoice'):
                res[_tax.id] = _account.invoice_realisation_account_id
            elif _invoice_type in ('in_refund', 'out_refund'):
                res[_tax.id] = _account.refund_realisation_account_id

        return isinstance(ids, (int, long, )) and res[ids] or res

    def find_tax_move(self, cr, uid, ids, context=None):
        res = {}
        if not context:
            context = {}
        select = ids
        if isinstance(select, (int, long, )):
            select = [ids]

        for _tax in self.pool.get('account.invoice.tax').browse(cr, uid, select, context=context):
            res[_tax.id] = False
            _tax_move_lines = _tax.invoice_id and _tax.invoice_id.move_id and _tax.invoice_id.move_id.line_id
            for move_line in _tax_move_lines:
                if ((move_line.account_id.id == _tax.account_id.id)
                    and ((move_line.debit == abs(_tax.amount))
                        or (move_line.credit == abs(_tax.amount))
                        or abs(move_line.amount_currency) == abs(_tax.amount))):
                    res[_tax.id] = move_line
                    break

        return isinstance(ids, (int, long, )) and res[ids] or res

    def realise_tax(self, cr, uid, ids, realizaton_date=date.today().strftime('%Y-%m-%d'), context=None):
        if not context:
            context = {}
        select = ids
        if isinstance(select, (int, long, )):
            select = [ids]

        obj_move = self.pool.get('account.move')
        obj_move_line = self.pool.get('account.move.line')
        obj_period = self.pool.get('account.period')

        for _tax in self.pool.get('account.invoice.tax').browse(cr, uid, select, context=context):
            # FIND PERIOD
            period_ids = obj_period.find(cr, uid, realizaton_date, context=context)
            period_id = period_ids and period_ids[0] or False

            # FIND DEBIT AND CREDIT ACCOUNT
            _doc_name = (_tax.invoice_id and (_tax.invoice_id.type in ('in_invoice', 'out_invoice')) and 'invoice') or 'refund'
            account_realise_id = _tax.get_realisation_account()[_tax.id]
            if not account_realise_id:
                if isinstance(ids, (int, long, )) or (len(ids) == 1):
                    raise osv.except_osv(_('Error!'), _('No %s tax realisation account defined for %s.') % (_doc_name, _tax.account_id.code))
                continue

            # FIND JOURNAL
            journal_id = _tax.get_realisation_journal()[_tax.id]
            if not journal_id:
                if isinstance(ids, (int, long, )) or (len(ids) == 1):
                    raise osv.except_osv(_('Error!'), _('No %s tax realisation journal defined for %s') % (_doc_name, _tax.account_id.code))
                continue

            # CANNOT REALIZE TAX LINE THAT HAS BEEN REALIZED
            if _tax.realise_move_id:
                if isinstance(ids, (int, long, )) or (len(ids) == 1):
                    raise osv.except_osv(_('Warning!'), _('Tax can only be realised once.'))
                continue

            # DETERMINE DEBIT / CREDIT ACCOUNT
            move_tax = _tax.find_tax_move()[_tax.id]
            if not move_tax:
                if isinstance(ids, (int, long, )) or (len(ids) == 1):
                    raise osv.except_osv(_('Error!'), _('Cannot find tax move!!!'))
                continue

            val_line = move_tax and move_tax.read()[0] or {}
            val_line = val_line and prep_dict_for_write(cr, uid, val_line, context=context) or {}
            for k in val_line.keys():
                if k not in ('currency_id', 'partner_id', 'tax_amount', 'product_id', 'account_tax_id', 'product_uom_id', 'quantity'):
                    del val_line[k]

            debit_account_id = ((move_tax.debit != 0.00) and account_realise_id.id) or move_tax.account_id.id
            credit_account_id = ((move_tax.credit != 0.00) and account_realise_id.id) or move_tax.account_id.id

            # CREATE MOVE
            val_move = {
                'date': realizaton_date,
                'journal_id': journal_id.id,
                'period_id': period_id,
            }
            realise_move_id = obj_move.create(cr, uid, val_move, context=context)
            _tax.write({'realise_move_id': realise_move_id})

            # CREATE DEBIT LINE
            val_line_debit = val_line.copy()
            val_line_debit.update({
                'name': 'Tax realisation - %s' % (move_tax.name),
                'debit': abs(move_tax.debit - move_tax.credit),
                'credit': 0.0,
                'account_id': debit_account_id,
                'period_id': period_id,
                'journal_id': journal_id.id,
                'move_id': realise_move_id,
                'amount_currency': abs(move_tax.amount_currency),
                'date': realizaton_date,
            })
            line_debit_id = obj_move_line.create(cr, uid, val_line_debit, context=context)

            # CREDIT LINE
            val_line_credit = val_line.copy()
            val_line_credit.update({
                'name': 'Tax realisation - %s' % (move_tax.name),
                'debit': 0.0,
                'credit': abs(move_tax.debit - move_tax.credit),
                'account_id': credit_account_id,
                'period_id': period_id,
                'journal_id': journal_id.id,
                'move_id': realise_move_id,
                'amount_currency': -1.0 * abs(move_tax.amount_currency),
                'date': realizaton_date,
            })
            line_credit_id = obj_move_line.create(cr, uid, val_line_credit, context=context)

            # POST MOVE
            obj_move.post(cr, uid, [realise_move_id], context=context)

            # RECONCILE
            reconcile_ids = []
            reconcile_ids.append(move_tax.id)
            reconcile_ids.append(((move_tax.debit != 0.0) and line_credit_id) or line_debit_id)
            obj_move_line.reconcile_partial(cr, uid, reconcile_ids)

        return True

    def create_taxform(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        select = ids
        if isinstance(select, (int, long, )):
            select = [ids]

        for _tax in self.pool.get('account.invoice.tax').browse(cr, uid, select, context=context):
            if (_tax.invoice_id and (_tax.invoice_id.type == 'out_invoice') and (not _tax.realise_move_id)):
                # Tax need to be realized first if it is customer invoice (out_invoice)
                if isinstance(ids, (int, long, )) or (len(ids) == 1):
                    raise osv.except_osv(_('Error!'), _('Tax %s need to be realized first.') % (_tax.name))
            else:
                ctx = context.copy()
                ctx.update({'taxform_date': _tax.realise_move_id and _tax.realise_move_id.date or date.today().strftime('%Y-%m-%d')})
                super(account_invoice_tax, self).create_taxform(cr, uid, _tax.id, context=ctx)

        return True

    def view_realisation_entry(self, cr, uid, ids, context=None):
        if not ids:
            return []
        _obj = self.browse(cr, uid, ids[0], context=context)
        return {
            'name': _("Realization Entry"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'res_id': _obj.realise_move_id.id,
        }

account_invoice_tax()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

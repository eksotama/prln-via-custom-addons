# -*- coding: utf-8 -*-
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

from lxml import etree
from osv import osv, fields, orm
import decimal_precision as dp
import time
from tools.translate import _
import netsvc
from account import account
from via_cash_advance.cash_advance_establishment import cash_advance_establishment

def _get_period(obj, cr, uid, context=None):
    periods = obj.pool.get('account.period').find(cr, uid)
    if periods:
        return periods[0]
    return False

def _get_amount(obj, cr, uid, context=None):
    if context is None:
        context = {}

    if ('via_cash_advance.line_type' not in context
        or 'via_cash_advance.establishment_id' not in context):
        return 0

    line_type = context['via_cash_advance.line_type']
    if line_type not in ('topup', 'disbursement'):
        return 0

    establishment_id = int(context['via_cash_advance.establishment_id'])
    if not establishment_id:
        return 0
    establishment = obj.pool.get('cash.advance.establishment').browse(cr, uid,
                                                                      establishment_id,
                                                                      context=context)

    outstanding = establishment.outstanding
    if line_type == 'topup' and outstanding < 0:
        return abs(outstanding)
    elif line_type == 'disbursement' and outstanding > 0:
        return outstanding
    else:
        return 0        

def validate_line_type(line_type):
    if line_type not in ('expense', 'topup', 'disbursement'):
        raise osv.except_osv(_('Error !'),
                             _('Unknown line type %s' % line_type))

class account_move(osv.osv):
    _inherit = "account.move"
    def post(self, cr, uid, ids, context=None):
        res = account.account_move.post(self, cr, uid, ids, context)
        # If a move line of an establishment line is posted, confirm the
        # establishment line automatically
        line_pool = self.pool.get('cash.advance.establishment.line')
        lines = line_pool.search(cr, uid, [('journal_entry','in',ids),
                                           ('journal_entry.state','=','posted'),
                                           ('state','=','pending')],
                                 context=context)
        wf_service = netsvc.LocalService("workflow")
        for l in line_pool.browse(cr, uid, lines, context=context):
            wf_service.trg_validate(1, 'cash.advance.establishment.line',
                                    l.id, 'line_confirm', cr)
        return res
    def unlink(self, cr, uid, ids, context=None):
        line_pool = self.pool.get('cash.advance.establishment.line')
        lines = line_pool.search(cr, uid, [('journal_entry','in',ids)],
                                 context=context)
        wf_service = netsvc.LocalService("workflow")
        for l in line_pool.browse(cr, uid, lines, context=context):
            wf_service.trg_validate(1, 'cash.advance.establishment.line',
                                    l.id, 'line_rejected', cr)
        return account.account_move.unlink(self, cr, uid, ids, context)
account_move()

class cash_advance_establishment_line(osv.osv):
    _name = 'cash.advance.establishment.line'
    _description = 'Cash Advance Establishment Line'
    __doc__ = 'The object to track the transactions of a cash advance establishment.'
    _columns = {
        'establishment': fields.many2one('cash.advance.establishment',
                                         'Establishment', required=True,
                                         readonly=True),
        'company': fields.related('establishment', 'company',
                                  type='many2one',
                                  relation='res.company',
                                  string='Company', store=True, readonly=True,
                                  required=True),
        'topup_disbursement_journal': fields.many2one('account.journal', 'Journal',
                                                      readonly=True,
                                                      states={'new': [('readonly', False)],
                                                              'draft': [('readonly', False)]},
                                                      domain=[('type','in',('cash','bank'))]),
        'period': fields.many2one('account.period', 'Period', required=True,
                                  readonly=True,
                                  domain="[('state','=','draft')]",
                                  states={'new': [('readonly', False)],
                                          'draft': [('readonly', False)]}),
        'date': fields.date('Date', required=True, readonly=True,
                            states={'new': [('readonly', False)],
                                    'draft': [('readonly', False)]}),
        'name': fields.char('Description', size=64, readonly=True, required=True,
                            states={'new': [('readonly', False)],
                                    'draft': [('readonly', False)]}),
        'ref': fields.char('Reference', size=64, readonly=True,
                           states={'new': [('readonly', False)],
                                   'draft': [('readonly', False)]}),
        'product': fields.many2one('product.product', 'Product',
                                   domain="[('active','=',True)]",
                                   readonly=True,
                                   states={'new': [('readonly', False)],
                                           'draft': [('readonly', False)]}),
        'expense_account': fields.many2one('account.account', 'Expense Account',
                                           readonly=True,
                                           states={'new': [('readonly', False)],
                                                   'draft': [('readonly', False)]},
                                           domain=[('type','!=','view'),
                                                   ('type','!=','consolidation'),
                                                   ('active','=',True)],),
        'amount': fields.float('Amount',
                               digits_compute=dp.get_precision('Account'),
                               required=True, readonly=True,
                               states={'new': [('readonly', False)],
                                       'draft': [('readonly', False)]}),
        'line_type': fields.selection([('topup', 'Top-up'),
                                       ('expense', 'Expense'),
                                       ('disbursement', 'Disbursement')],
                                      'Line Type',
                                      required=True, select=0),
        'narration': fields.text('Narration', readonly=True,
                                 states={'new': [('readonly', False)],
                                         'draft': [('readonly', False)]}),
        # TP: The state 'new' is used only to prevent buttons from appearing
        #     during object creation. Without this, user is not forced to
        #     press 'save & close' but can click one of the button that will
        #     result in a harmless error for the system but very annoying one
        #     for the user.
        'state': fields.selection([('new', 'Draft'),
                                   ('draft', 'Draft'),
                                   ('pending', 'Pending Approval'),
                                   ('done', 'Done/Approved'),
                                   ('cancel', 'Cancelled'),
                                   ('rejected', 'Rejected')], 'State',
                                  required=True, readonly=True, select=1),
        'journal_entry': fields.many2one('account.move', 'Journal Entry',
                                         readonly=True, select=1),
    }

    _defaults = {
        'state': 'new',
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'line_type': lambda self, cr, uid, c: c.get('via_cash_advance.line_type', None),
        'company': (lambda self, cr, uid, c: self.pool.get('res.users')
                    .browse(cr, uid, uid, c).company_id.id),
        'period': _get_period,
        'amount': _get_amount,
    }

    def unlink(self, cr, uid, ids, context=None):
        lines = self.read(cr, uid, ids, ['state'], context=context)
        for l in lines:
            if l['state'] not in ['draft', 'cancel']:
                raise osv.except_osv(_('Invalid action !'),
                                     _('Cannot delete line(s) which are not draft/cancelled !'))
        for x in self.update_establishments(cr, uid, ids, context, wait_deletion=True):
            super(cash_advance_establishment_line, self).unlink(cr, uid, ids, context)
        return True

    def create(self, cr, uid, vals, context=None):
        if 'amount' in vals and vals['amount'] < 0:
            raise osv.except_osv(_('Invalid value !'),
                                 _("Amount of '%s' is negative" % vals['name']))
        vals['state'] = 'draft'
        res = super(cash_advance_establishment_line, self).create(cr, uid, vals,
                                                                  context=context)
        for x in self.update_establishments(cr, uid, [res], context):
            pass
        return res

    # Update the stored function fields in the establishments
    def update_establishments(self, cr, uid, line_ids, context=None, wait_deletion=False):
        est_ids = set()
        for e in self.browse(cr, uid, line_ids, context=context):
            if e.establishment:
                est_ids.add(e.establishment.id)
        if wait_deletion:
            yield
        self.pool.get('cash.advance.establishment').write(cr, uid,
                                                          list(est_ids), {},
                                                          context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}

        if 'via_cash_advance.exec_wkf_confirm' not in context:
            # Cater to OERP 6.1 behavior of keeping updating the foreign key
            # field even when there is no change to the child record.
            oerp_61_quirk = (len(vals) == 1 and 'establishment' in vals)

            if filter(lambda o: (o.state != 'draft'
                                 and not (oerp_61_quirk
                                          and o.establishment.id == vals['establishment'])),
                      self.browse(cr, uid, ids, context=context)):
                raise osv.except_osv(_('Error !'),
                                     _('You can only edit a draft establishment line'))

            if 'amount' in vals and vals['amount'] < 0:
                raise osv.except_osv(_('Invalid value !'),
                                     _('Amount cannot be negative !'))

        else:
            del context['via_cash_advance.exec_wkf_confirm']

        res = super(cash_advance_establishment_line, self).write(cr, uid, ids, vals,
                                                                 context=context)
        for x in self.update_establishments(cr, uid, ids, context):
            pass
        return res

    def onchange_product(self, cr, uid, ids, product=False, context=None):
        res = {
            'value': {},
        }

        if not product:
            return res

        prod_obj = self.pool.get('product.product').browse(cr, uid, [product],
                                                           context=context)
        if prod_obj:
            res['value'].update({
                'name': prod_obj[0].name_template,
                'expense_account': ((prod_obj[0].property_account_expense
                                     and prod_obj[0].property_account_expense.id)
                                    or (prod_obj[0].categ_id
                                        and prod_obj[0].categ_id.property_account_expense_categ
                                        and prod_obj[0].categ_id.property_account_expense_categ.id)),
                'amount': prod_obj[0].standard_price,
            })

        return res

    def action_pending(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        currency_pool = self.pool.get('res.currency')

        for o in self.browse(cr, uid, ids, context=context):
            if o.journal_entry:
                continue

            journal = None
            debit_account = None
            credit_account = None
            if o.line_type == 'expense':
                journal = o.establishment.cash_advance_journal
                debit_account = (o.expense_account
                                 or o.product.property_account_expense
                                 or (o.product.categ_id
                                     and o.product.categ_id.property_account_expense_categ))
                if not debit_account:
                    raise osv.except_osv(_('Error !'),
                                         _('Please specify the product expense account'))
            elif o.line_type in ('topup', 'disbursement'):
                journal = o.topup_disbursement_journal
                if o.line_type == 'topup':
                    debit_account_journal = o.establishment.cash_advance_journal
                else:
                    debit_account_journal = journal
                debit_account = debit_account_journal.default_debit_account_id
                if not debit_account:
                    raise osv.except_osv(_('Error !'),
                                         _('Please define a default debit account on journal %s !'
                                           % debit_account_journal.name))
            else:
                raise osv.except_osv(_('Error !'),
                                     _('Unknown line type %s' % o.line_type))
            if o.line_type in ('expense', 'topup'):
                credit_account_journal = journal
            else:
                credit_account_journal = o.establishment.cash_advance_journal
            credit_account = credit_account_journal.default_credit_account_id
            if not credit_account:
                raise osv.except_osv(_('Error !'),
                                     _('Please define a default credit account on journal %s !'
                                       % credit_account_journal.name))

            context_multi_currency = context.copy()
            context_multi_currency.update({'date': o.date})

            move = {
                'name': '/',
                'journal_id': journal.id,
                'narration': o.establishment.note,
                'date': o.date,
                'ref': o.ref,
                'period_id': o.period and o.period.id or False
            }
            move_id = move_pool.create(cr, uid, move)

            # Create the lines
            company_currency = journal.company_id.currency_id.id
            current_currency = o.establishment.currency.id
            posted_amount = currency_pool.compute(cr, uid, current_currency, company_currency, o.amount, context=context_multi_currency)

            ## Debit line
            move_line_debit = {
                'move_id': move_id,
                'journal_id': journal.id,
                'period_id': o.period.id,
                'currency_id': company_currency <> current_currency and current_currency or False,
                'amount_currency': company_currency <> current_currency and o.amount or 0.0,
                'date': o.date,
                'name': o.name,

                'debit': posted_amount,
                'account_id': debit_account.id,
            }
            move_line_pool.create(cr, uid, move_line_debit)

            ## Credit line
            move_line_credit = move_line_debit
            del move_line_credit['debit']
            move_line_credit['credit'] = posted_amount
            move_line_credit['account_id'] = credit_account.id
            move_line_pool.create(cr, uid, move_line_credit)

        self.write(cr, uid, ids, {
            'state': 'pending',
            'journal_entry': move_id,
        }, context=context)

        wf_service = netsvc.LocalService("workflow")
        for id in set([o.establishment.id for o in filter(lambda r: r.establishment.state == 'draft', self.browse(cr, uid, ids, context=context))]):
            wf_service.trg_validate(uid, 'cash.advance.establishment', id, 'establishment_open', cr)

    def action_confirm(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        context.update({'via_cash_advance.exec_wkf_confirm': True})
        self.write(cr, uid, ids, {'state': 'done'}, context=context)

    def action_rejected(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        context.update({'via_cash_advance.exec_wkf_confirm': True})
        self.write(cr, uid, ids, {'state': 'rejected'}, context=context)

    def action_cancel(self, cr, uid, ids, context=None):
        draft_ids = []
        pending_ids = []
        for o in self.browse(cr, uid, ids, context=context):
            if o.state == 'draft':
                draft_ids.append(o.id)
            elif o.state == 'pending':
                pending_ids.append(o.id)

            if not o.journal_entry:
                continue
            o.journal_entry.button_cancel()

        self.write(cr, uid, draft_ids, {'state': 'cancel'}, context=context)

        if context is None:
            context = {}
        context.update({'via_cash_advance.exec_wkf_confirm': True})
        self.write(cr, uid, pending_ids, {'state': 'cancel'}, context=context)

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        if context is None:
            context = {}

        line_name = {
            '': 'Cash Advance Lines',
            'topup': 'Top-ups',
            'disbursement': 'Disbursements',
            'expense': 'Expenses',
        }
        line_type = context.get('via_cash_advance.line_type', '')

        result = super(cash_advance_establishment_line, self).fields_view_get(cr, uid, view_id,
                                                                              view_type,
                                                                              context=context,
                                                                              toolbar=toolbar,
                                                                              submenu=submenu)

        def _set_attr(field_name, attr_name, attr_value, in_tree_view):
            field = arch.find('.//field[@name="' + field_name + '"]')
            if field is not None:
                field.attrib[attr_name] = attr_value
                if hasattr(orm, 'setup_modifiers'):
                    orm.setup_modifiers(field, context=context,
                                        in_tree_view=in_tree_view)
        def _activate_attr(field_name, attr_name, in_tree_view):
            _set_attr(field_name, attr_name, 'True', in_tree_view)

        def _make_invisible(field_name, in_tree_view=False):
            _activate_attr(field_name, 'invisible', in_tree_view)
        def _make_required(field_name, in_tree_view=False):
            _activate_attr(field_name, 'required', in_tree_view)
        def _set_string(field_name, string, in_tree_view=False):
            _set_attr(field_name, 'string', string, in_tree_view)

        if view_type == 'form':
            arch = etree.XML(result['arch'])
            arch.attrib['string'] = line_name[line_type][:-1]

            if line_type == 'expense':
                _make_invisible('topup_disbursement_journal')
                _make_required('expense_account')
            elif line_type == 'topup':
                _set_string('topup_disbursement_journal', 'Top-up from')
            elif line_type == 'disbursement':
                _set_string('topup_disbursement_journal', 'Disburse to')
            else:
                raise osv.except_osv(_('Invalid action !'),
                                     _('Unknown line type %s' % line_type))

            if line_type in ('topup', 'disbursement'):
                field = arch.find('.//field[@name="topup_disbursement_journal"]')
                if field is not None:
                    field.attrib['required'] = 'True'
                    if hasattr(orm, 'setup_modifiers'):
                        orm.setup_modifiers(field, context=context)

                    ca_journal_id = context.get('via_cash_advance.cash_advance_journal_id', None) or None
                    if ca_journal_id is None:
                        raise osv.except_osv(_('Error !'),
                                             _('Select an establishment journal first before creating any %s'
                                               % line_type))
                    else:
                        get_journal_currency = cash_advance_establishment.get_journal_currency
                        establishment_pool = self.pool.get('cash.advance.establishment')
                        ca_journal_curr_id = get_journal_currency(establishment_pool, cr, uid,
                                                                  ca_journal_id, context=context)
                        sels = result['fields']['topup_disbursement_journal']['selection']
                        sels = filter(lambda s: ((s[0] != ca_journal_id)
                                                 and ((type(s[0]) in (int, str, unicode))
                                                      and (ca_journal_curr_id == get_journal_currency(establishment_pool,
                                                                                                      cr, uid, s[0],
                                                                                                      context=context)))
                                                 or (type(s[0]) not in (int, str, unicode))),
                                      sels)
                        result['fields']['topup_disbursement_journal']['selection'] = sels

                _make_invisible('product')
                _make_invisible('expense_account')

            result['arch'] = etree.tostring(arch, pretty_print=True)
        elif view_type == 'tree':
            arch = etree.XML(result['arch'])
            if line_type == 'expense':
                arch.attrib['string'] = line_name[line_type]
                arch.attrib['editable'] = 'bottom'
                _make_required('expense_account', in_tree_view=True)
            elif line_type in ('topup', 'disbursement'):
                arch.attrib['string'] = line_name[line_type]
                _make_invisible('product', in_tree_view=True)
                _make_invisible('expense_account', in_tree_view=True)
                _make_invisible('period', in_tree_view=True)
                _make_invisible('ref', in_tree_view=True)
                _make_invisible('narration', in_tree_view=True)
            else:
                raise osv.except_osv(_('Invalid action !'),
                                     _('Unknown line type %s' % line_type))
            result['arch'] = etree.tostring(arch, pretty_print=True)

        return result

cash_advance_establishment_line()

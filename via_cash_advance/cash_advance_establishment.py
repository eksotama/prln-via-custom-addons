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

from osv import osv, fields
import decimal_precision as dp
from cash_advance_journal_selection import get_ca_journal_selection
from tools.translate import _

def _get_balance(obj, cr, uid, ids, name, arg, context=None):
    res = dict.fromkeys(ids, {
        'inflow': 0,
        'outflow': 0,
        'outstanding': 0,
    })

    inflow_sql = (" SELECT l.establishment, SUM(l.amount) AS amount"
                  " FROM cash_advance_establishment_line l"
                  "  INNER JOIN account_move m"
                  "   ON l.journal_entry = m.id"
                  " WHERE l.line_type = 'topup'"
                  "  AND m.state = 'posted'"
                  "  AND l.establishment IN %s"
                  " GROUP BY l.establishment")
    outflow_sql = (" SELECT l.establishment, SUM(l.amount) AS amount"
                   " FROM cash_advance_establishment_line l"
                   "  INNER JOIN account_move m"
                   "   ON l.journal_entry = m.id"
                   " WHERE l.line_type IN ('disbursement', 'expense')"
                   "  AND m.state = 'posted'"
                   "  AND l.establishment IN %s"
                   " GROUP BY l.establishment")

    cr.execute(" SELECT"
               "  COALESCE(inflow.establishment, outflow.establishment),"
               "  COALESCE(inflow.amount, 0),"
               "  COALESCE(outflow.amount, 0),"
               "  COALESCE(inflow.amount, 0) - COALESCE(outflow.amount, 0)"
               " FROM"
               "  (%s) inflow"
               "  FULL OUTER JOIN (%s) outflow"
               "   ON inflow.establishment = outflow.establishment"
               % (inflow_sql, outflow_sql), (tuple(ids), tuple(ids)))

    if cr.rowcount >= 1:
        update_data = {}
        for rec in cr.fetchall():
            update_data[rec[0]] = {
                'inflow': rec[1],
                'outflow': rec[2],
                'outstanding': rec[3],
            }
        res.update(update_data)

    return res

class cash_advance_establishment(osv.osv):
    _name = 'cash.advance.establishment'
    _description = 'Cash Advance Establishment'
    __doc__ = 'The object to track a cash advance given to an employee.'
    _columns = {
        'name': fields.char('Reference', size=64, required=True,
                            readonly=True, states={'draft': [('readonly', False)]},
                            select=1),
        'employee': fields.many2one('hr.employee', 'Employee', required=True,
                                    readonly=True,
                                    domain="[('company_id','child_of',company),('resource_id.active','=',True)]",
                                    states={'draft': [('readonly', False)]},
                                    select=1),
        'company': fields.many2one('res.company', 'Company', required=True,
                                   readonly=True),
        'cash_advance_journal': fields.many2one('account.journal',
                                                'Journal',
                                                required=True, readonly=True,
                                                states={'draft': [('readonly', False)]},
                                                select=1),
        'note': fields.text('Note', translate=True, readonly=True,
                            states={'draft': [('readonly', False)]}),
        'top_ups': fields.one2many('cash.advance.establishment.line',
                                   'establishment', 'Top-ups',
                                   domain=[('line_type', '=', 'topup')],
                                   states={'done': [('readonly', True)]}),
        'expenses': fields.one2many('cash.advance.establishment.line',
                                    'establishment', 'Expenses',
                                    domain=[('line_type', '=', 'expense')],
                                    states={'done': [('readonly', True)]}),
        'disbursements': fields.one2many('cash.advance.establishment.line',
                                         'establishment', 'Disbursements',
                                         domain=[('line_type', '=', 'disbursement')],
                                         states={'done': [('readonly', True)]}),
        'outstanding': fields.function(_get_balance, method=True, type='float',
                                       string='Balance', store=True, multi='balance',
                                       help="The balance of all posted transactions"),
        'inflow': fields.function(_get_balance, method=True, string='Incoming', type='float',
                                  store=True, multi='balance',
                                  help="The total of posted top-ups"),
        'outflow': fields.function(_get_balance, method=True, string='Outgoing', type='float',
                                   store=True, multi='balance',
                                   help="The total of posted expenses and disbursements"),
        'state': fields.selection([('draft', 'Draft'),
                                   ('open', 'Open'),
                                   ('done', 'Done')], 'State',
                                  required=True, readonly=True, select=1),
        'currency': fields.many2one('res.currency', 'Currency', required=True, readonly=True),
    }

    _defaults = {
        'state': 'draft',
        'company': (lambda self, cr, uid, c: self.pool.get('res.users')
                    .browse(cr, uid, uid, c).company_id.id),
    }

    def get_journal_currency(self, cr, uid, journal_id, context=None):
        journal_id = int(journal_id)
        journal_obj = self.pool.get('account.journal').browse(cr, uid, [journal_id],
                                                              context=context)
        if not journal_obj:
            return None

        return (journal_obj[0].currency and journal_obj[0].currency.id
                or journal_obj[0].company_id.currency_id.id)

    def onchange_ca_journal(self, cr, uid, ids, ca_journal=False, context=None):
        res = {
            'value': {},
        }

        if not ca_journal:
            return res

        res['value'].update({
            'currency': self.get_journal_currency(cr, uid, ca_journal,
                                                  context=context),
        })

        return res

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        if context is None:
            context = {}

        result = super(cash_advance_establishment, self).fields_view_get(cr, uid, view_id,
                                                                         view_type,
                                                                         context=context,
                                                                         toolbar=toolbar,
                                                                         submenu=submenu)
        if 'cash_advance_journal' in result['fields']:
            ca_journal_selection = get_ca_journal_selection(self, cr, uid, context)
            if ca_journal_selection:
                result['fields']['cash_advance_journal']['selection'] = ca_journal_selection
            else:
                result['fields']['cash_advance_journal']['selection'] = [('', '')]

        return result

    def create(self, cr, uid, vals, context=None):
        if 'cash_advance_journal' in vals:
            vals.update({
                'currency': self.get_journal_currency(cr, uid,
                                                      vals['cash_advance_journal'],
                                                      context=context)
            })

        # The following code ensures that an expense line cannot have a journal
        # while a top-up or a disbursement line must have a journal that is set
        # to a journal other than the one used by the establishment itself.
        O2M_VALS_IDX = 2
        if 'expenses' in vals:
            for line in vals['expenses']:
                l_vals = line[O2M_VALS_IDX]
                l_vals['line_type'] = 'expense'
                if ('topup_disbursement_journal' in l_vals
                    and l_vals['topup_disbursement_journal']):
                    raise osv.except_osv(_('Error !'),
                                         _("Expense line '%s' cannot have a journal!"
                                           % l_vals['name']))
        if 'top_ups' in vals:
            for line in vals['top_ups']:
                l_vals = line[O2M_VALS_IDX]
                l_vals['line_type'] = 'topup'
                if (('topup_disbursement_journal' not in l_vals)
                    or (not l_vals['topup_disbursement_journal'])
                    or (l_vals['topup_disbursement_journal']
                        == vals['cash_advance_journal'])):
                    raise osv.except_osv(_('Error !'),
                                         _("Topup line '%s' journal must be set"
                                           " and be different from the establishment journal!"
                                           % l_vals['name']))
        if 'disbursements' in vals:
            for line in vals['disbursements']:
                l_vals = line[O2M_VALS_IDX]
                l_vals['line_type'] = 'disbursement'
                if (('topup_disbursement_journal' not in l_vals)
                    or (not l_vals['topup_disbursement_journal'])
                    or (l_vals['topup_disbursement_journal']
                        == vals['cash_advance_journal'])):
                    raise osv.except_osv(_('Error !'),
                                         _("Disbursement line '%s' journal must be set"
                                           " and be different from the establishment journal!"
                                           % l_vals['name']))

        return super(cash_advance_establishment, self).create(cr, uid, vals,
                                                              context=context)

    def write(self, cr, uid, ids, vals, context=None):
        ca_journal_updated = ('cash_advance_journal' in vals)
        if ca_journal_updated:
            vals.update({
                'currency': self.get_journal_currency(cr, uid,
                                                      vals['cash_advance_journal'],
                                                      context=context)
            })

        changed_attrs = set(vals.keys())
        changed_attrs.discard('expenses')
        changed_attrs.discard('top_ups')
        changed_attrs.discard('disbursements')
        changed_attrs.discard('state')

        if changed_attrs:
            for e in self.browse(cr, uid, ids, context=context):
                if e.state != 'draft':
                    # Only allow changes to establishment status & lines
                    raise osv.except_osv(_('Error !'),
                                         _('Establishment state has changed !'
                                           ' Please cancel your edit !'))

        # A small fraction of the following code is just to set the line_type
        # of a new establishment line into the right one. The major fraction
        # ensures that an expense line cannot have a journal while a top-up or
        # a disbursement line must have a journal that is set to a journal
        # other than the one used by the establishment itself.
        def _get_line_name():
            if 'name' in l_vals:
                return l_vals['name']
            else:
                l_pool = self.pool.get('cash.advance.establishment.line')
                return l_pool.browse(cr, uid, line[O2M_ID_IDX], context=context).name

        O2M_CODE_IDX = 0
        O2M_ID_IDX = 1
        O2M_VALS_IDX = 2
        CREATE_CODE = 0
        UPDATE_CODE = 1
        if 'expenses' in vals:
            for line in vals['expenses']:
                if line[O2M_CODE_IDX] == CREATE_CODE:
                    l_vals = line[O2M_VALS_IDX]
                    l_vals['line_type'] = 'expense'
                    if ('topup_disbursement_journal' in l_vals
                        and l_vals['topup_disbursement_journal']):
                        raise osv.except_osv(_('Error !'),
                                             _("Expense line '%s' cannot have a journal!"
                                               % l_vals['name']))
                if line[O2M_CODE_IDX] == UPDATE_CODE:
                    l_vals = line[O2M_VALS_IDX]
                    if ('topup_disbursement_journal' in l_vals
                        and l_vals['topup_disbursement_journal']):
                        raise osv.except_osv(_('Error !'),
                                             _("Expense line '%s' cannot have a journal!"
                                               % _get_line_name()))

        top_ups_to_check = {}
        disbursements_to_check = {}
        if ca_journal_updated:
            ca_journal_ids = [vals['cash_advance_journal']]
            for e in self.browse(cr, uid, ids, context):
                for l in e.top_ups:
                    top_ups_to_check[l.id] = (l.topup_disbursement_journal.id,
                                              l.name)
                for l in e.disbursements:
                    disbursements_to_check[l.id] = (l.topup_disbursement_journal.id,
                                                    l.name)
        else:
            ca_journal_ids = [e.cash_advance_journal.id
                              for e in self.browse(cr, uid, ids, context)]
        if 'top_ups' in vals:
            for line in vals['top_ups']:
                if line[O2M_CODE_IDX] == CREATE_CODE:
                    l_vals = line[O2M_VALS_IDX]
                    l_vals['line_type'] = 'topup'
                    if (('topup_disbursement_journal' not in l_vals)
                        or (not l_vals['topup_disbursement_journal'])
                        or (l_vals['topup_disbursement_journal']
                            in ca_journal_ids)):
                        raise osv.except_osv(_('Error !'),
                                             _("Topup line '%s' journal must be set"
                                               " and be different from the establishment journal!"
                                               % l_vals['name']))
                if line[O2M_CODE_IDX] == UPDATE_CODE:
                    l_vals = line[O2M_VALS_IDX]
                    if (('topup_disbursement_journal' in l_vals)
                        and ((not l_vals['topup_disbursement_journal'])
                             or (l_vals['topup_disbursement_journal']
                                 in ca_journal_ids))):
                        raise osv.except_osv(_('Error !'),
                                             _("Topup line '%s' journal must be set"
                                               " and be different from the establishment journal!"
                                               % _get_line_name()))
                    elif ca_journal_updated and 'topup_disbursement_journal' in l_vals:
                        del top_ups_to_check[line[O2M_ID_IDX]]
        for l in top_ups_to_check.itervalues():
            # This can only be entered when ca_journal_updated is true
            if l[0] == ca_journal_ids[0]:
                raise osv.except_osv(_('Error !'),
                                     _("Topup line '%s' journal must be"
                                       " different from the establishment journal!"
                                       % l[1]))

        if 'disbursements' in vals:
            for line in vals['disbursements']:
                if line[O2M_CODE_IDX] == CREATE_CODE:
                    l_vals = line[O2M_VALS_IDX]
                    l_vals['line_type'] = 'disbursement'
                    if (('topup_disbursement_journal' not in l_vals)
                        or (not l_vals['topup_disbursement_journal'])
                        or (l_vals['topup_disbursement_journal']
                            in ca_journal_ids)):
                        raise osv.except_osv(_('Error !'),
                                             _("Disbursement line '%s' journal must be set"
                                               " and be different from the establishment journal!"
                                               % l_vals['name']))
                if line[O2M_CODE_IDX] == UPDATE_CODE:
                    l_vals = line[O2M_VALS_IDX]
                    if (('topup_disbursement_journal' in l_vals)
                        and ((not l_vals['topup_disbursement_journal'])
                             or (l_vals['topup_disbursement_journal']
                                 in ca_journal_ids))):
                        raise osv.except_osv(_('Error !'),
                                             _("Disbursement line '%s' journal must be set"
                                               " and be different from the establishment journal!"
                                               % _get_line_name()))
                    elif ca_journal_updated and 'topup_disbursement_journal' in l_vals:
                        del disbursements_to_check[line[O2M_ID_IDX]]
        for l in disbursements_to_check.itervalues():
            # This can only be entered when ca_journal_updated is true
            if l[0] == ca_journal_ids[0]:
                raise osv.except_osv(_('Error !'),
                                     _("Disbursement line '%s' journal must be"
                                       " different from the establishment journal!"
                                       % l[1]))

        return super(cash_advance_establishment, self).write(cr, uid, ids, vals, context=context)

    def action_open(self, cr, uid, ids, context=None):
        if context is not None:
            raise osv.except_osv(_('Error !'),
                                 _('Cash Advance Establishment cannot be opened'
                                   ' manually'))
        self.write(cr, uid, ids, {'state': 'open'}, context=context)

    def action_close(self, cr, uid, ids, context=None):
        # All establishment lines must be done or canceled
        line_ids = set()
        for o in self.browse(cr, uid, ids, context=context):
            topup_ids = set(map(lambda x: x.id, o.top_ups))
            expense_ids = set(map(lambda x: x.id, o.expenses))
            disbursement_ids = set(map(lambda x: x.id, o.disbursements))
            line_ids = line_ids.union(topup_ids).union(expense_ids).union(disbursement_ids)

        line_pool = self.pool.get('cash.advance.establishment.line')
        for l in line_pool.browse(cr, uid, list(line_ids), context=context):
            if l.state == 'pending' or l.state == 'draft':
                raise osv.except_osv(_('Error !'),
                                     _('%s %s "%s" prevents closing !'
                                       % (l.state.capitalize(), l.line_type, l.name)))

        # Outstanding balance must be zero
        currency_pool = self.pool.get('res.currency')
        if filter(lambda e: not currency_pool.is_zero(cr, uid, e.currency,
                                                      e.outstanding),
                  self.browse(cr, uid, ids, context=context)):
            raise osv.except_osv(_('Error !'),
                                 _('Outstanding balance is not zero !'))

        self.write(cr, uid, ids, {'state': 'done'}, context=context)

cash_advance_establishment()

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
from tools.translate import _

def get_ca_journal_selection(obj, cr, uid, context=None):
    pool = obj.pool.get('cash.advance.journal.selection')
    ids = pool.search(cr, uid, [], context=context)
    objs = pool.browse(cr, uid, ids, context=context)
    return [(o.journal.id, o.journal.name) for o in objs]

class cash_advance_journal_selection(osv.osv):
    _name = 'cash.advance.journal.selection'
    _description = 'Cash Advance Journal Selection'
    __doc__ = ('The journals that can be used to record all cash advance'
               ' transactions.')
    _columns = {
        'company': fields.many2one('res.company', 'Company', required=True,
                                   readonly=True),
        'journal': fields.many2one('account.journal', 'Journal',
                                   required=True,
                                   domain=[('type','in',['cash','bank'])]),
    }
    _defaults = {
        'company': (lambda self, cr, uid, c: self.pool.get('res.users')
                    .browse(cr, uid, uid, c).company_id.id),
    }

    def create(self, cr, uid, vals, context=None):
        if 'journal' in vals:
            ids = self.search(cr, uid, [], context=context)
            journal_dir = {}
            for o in self.browse(cr, uid, ids, context=context):
                journal_dir[o.journal.id] = o.id
            if vals['journal'] in journal_dir:
                return journal_dir[vals['journal']]
        return super(cash_advance_journal_selection, self).create(cr, uid, vals,
                                                                  context)

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        res = super(cash_advance_journal_selection, self).fields_view_get(cr, uid, view_id,
                                                                          view_type,
                                                                          context=context,
                                                                          toolbar=toolbar,
                                                                          submenu=submenu)
        if 'journal' in res['fields'] and 'selection' in res['fields']['journal']:
            sels = res['fields']['journal']['selection']
            unused = []
            used = []
            ids = self.search(cr, uid, [], context=context)
            journal_ids = map(lambda o: o.journal.id,
                              self.browse(cr, uid, ids, context=context))
            for s in sels:
                k = s[0]
                if k is None:
                    continue
                if k in journal_ids:
                    used.append(s)
                else:
                    unused.append(s)
            new_sels = [(None, '')]
            new_sels.extend(unused)
            new_sels.append((None, '--- The following has been used ---'))
            new_sels.extend(used)
            res['fields']['journal']['selection'] = new_sels
        return res

cash_advance_journal_selection()

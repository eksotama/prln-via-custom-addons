###############################################################################
#
#  Vikasa Infinity Anugrah, PT
#  Copyright (C) 2012 Vikasa Infinity Anugrah <http://www.infi-nity.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see http://www.gnu.org/licenses/.
#
###############################################################################

from osv import osv, fields
import pooler
from via_reporting_tree import via_reporting_tree
from tools.translate import _

class data_point(object):
    def __init__(self):
        self.data = {}

class tree_node(object):
    def __init__(self, _id, name, level, data):
        self.id = _id
        self.name = name
        self.level = level
        self.data = data
        self.total_data = []
        self.children = []

        self.display_data = {}
    def is_leaf(self):
        return len(self.children) == 0
    def is_total_node(self):
        return len(self.total_data) != 0

class tree(object):
    heading_for_fusion = ['reconciled_income', 'unreconciled_income',
                          'prior_income',
                          'reconciled_expense', 'unreconciled_expense',
                          'prior_expense',
                          'residual_income', 'residual_expense']
    heading_for_total = ['beginning', 'ending', 'movement',
                         'total_income', 'total_expense']
    special_node_names = heading_for_fusion[0:-2] + heading_for_total

    def _construct_tree(self, reporting_tree):
        root_node = reporting_tree.root_node_id
        if not root_node:
            return None

        def upon_entering(node, context):
            node_data = self.node_data.get(node.id, [])

            if node.id in self.special_nodes_for_fusion:
                context['heading_names'] = self.special_nodes_for_fusion[node.id]

            for node_datum in node_data:
                fusing_point = data_point()
                if 'heading_names' in context:
                    acc_id = node_datum.account_id.id
                    for heading_name in context['heading_names']:
                        (key1, key2) = heading_name.split('_')
                        fusing_point = self.data_attachment_points[key1][key2].setdefault(acc_id, fusing_point)
                node_datum.data_point = fusing_point

            t_node = tree_node(node.id, node.name, node.level, node_data)
            if node.id in self.special_nodes_for_total:
                total_names = self.special_nodes_for_total[node.id]
                for total_name in total_names:
                    t_node.total_data.append(self.total_attachment_points[total_name])

            if 'node' not in context:
                context['node'] = t_node
            else:
                context['node'].children.append(t_node)
                context['node'] = t_node

        def before_leaving(node, context):
            if 'heading_name' in context:
                del context['heading_name']

        context = {}
        via_reporting_tree.tree.traverse(reporting_tree.root_node_id,
                                         upon_entering_fn=upon_entering,
                                         before_leaving_fn=before_leaving,
                                         context=context)
        return context['node']

    def validate_tree(self, cr, uid, reporting_tree, context=None):
        # All special nodes must be specified
        unset_special_nodes = set(self.special_node_names)
        for special_node in reporting_tree.special_node_ids:
            unset_special_nodes.remove(special_node.type_id.name)
        if len(unset_special_nodes) != 0:
            names = '", "'.join(str(n) for n in unset_special_nodes)
            raise osv.except_osv(_('Error !'),
                                 _('Special nodes "%s" are not set in tree %s.')
                                 % (names, reporting_tree.name))

    def __init__(self, cr, uid, reporting_tree_id, context=None):
        self.pool = pooler.get_pool(cr.dbname)

        # Resolve the given reporting tree ID
        tree_pool = self.pool.get('via.reporting.tree')
        _tree = tree_pool.browse(cr, uid, reporting_tree_id, context=context)

        # Validate tree
        self.validate_tree(cr, uid, _tree, context=context)

        # Index the special nodes
        self.special_nodes_for_fusion = {}
        self.special_nodes_for_total = {}
        for special_node in _tree.special_node_ids:
            special_nodes = None
            if special_node.type_id.name in self.heading_for_fusion:
                special_nodes = self.special_nodes_for_fusion
            elif special_node.type_id.name in self.heading_for_total:
                special_nodes = self.special_nodes_for_total

            if special_nodes is not None:
                l = special_nodes.setdefault(special_node.node_id.id, [])
                l.append(special_node.type_id.name)

        # Pull all node data
        tree_node_pool = self.pool.get('via.account.tree.node')
        crit = [('node_id.tree_id','=',_tree.id)]
        tree_node_ids = tree_node_pool.search(cr, uid, crit, context=context)
        tree_nodes = tree_node_pool.browse(cr, uid, tree_node_ids,
                                           context=context)
        self.node_data = {}
        for tree_node in tree_nodes:
            l = self.node_data.setdefault(tree_node.node_id.id, [])
            l.append(tree_node)

        # Construct the tree
        self.data_attachment_points = {
            'reconciled': {
                'income': {},
                'expense': {},
            },
            'unreconciled': {
                'income': {},
                'expense': {},
            },
            'prior': {
                'income': {},
                'expense': {},
            },
        }
        self.data_attachment_points['residual'] = {
            'income': self.data_attachment_points['unreconciled']['income'],
            'expense': self.data_attachment_points['unreconciled']['expense'],
        }
        self.total_attachment_points = {
            'beginning': data_point(),
            'ending': data_point(),
            'movement': data_point(),
            'total_income': data_point(),
            'total_expense': data_point(),
        }
        self.tree = self._construct_tree(_tree)
        self.company_ids_seen = set()
        self.period_ids_seen = set()

    def attach_data(self, tree_data, normalizer, rounder, is_zero):
        for datum in tree_data:
            self.company_ids_seen.add(datum['com_id'])
            self.period_ids_seen.add(datum['period_id'])

            typ = datum['type']
            attachment_point = None
            if typ in self.heading_for_total:
                attachment_point = self.total_attachment_points[typ]
            elif typ in self.heading_for_fusion:
                (key1, key2) = typ.split('_')
                key3 = datum['account_id']
                try:
                    attachment_point = self.data_attachment_points[key1][key2][key3]
                except KeyError:
                    # Reporting tree designer might not want this account to be
                    # included in the calculation.
                    continue

            if attachment_point is None:
                continue

            val = self._get_period_com_amount(attachment_point.data,
                                              datum['period_id'],
                                              datum['com_id'])
            self._set_period_com_amount(attachment_point.data,
                                        datum['period_id'],
                                        datum['com_id'],
                                        rounder(val + datum['amount']))

        # Calculate total income
        total_income = self.total_attachment_points['total_income'].data = {}
        reconciled_income = self.data_attachment_points['reconciled']['income']
        for (acc_id, v0) in reconciled_income.iteritems():
            for (period_id, v1) in v0.data.iteritems():
                for com_id in v1.iterkeys():
                    a = self._get_period_com_amount(total_income, period_id, com_id)
                    b = self._get_period_com_amount(v0.data, period_id, com_id)
                    self._set_period_com_amount(total_income, period_id, com_id,
                                                rounder(a + b))
        unreconciled_income = self.data_attachment_points['unreconciled']['income']
        for (acc_id, v0) in unreconciled_income.iteritems():
            for (period_id, v1) in v0.data.iteritems():
                for com_id in v1.iterkeys():
                    a = self._get_period_com_amount(total_income, period_id, com_id)
                    b = self._get_period_com_amount(v0.data, period_id, com_id)
                    self._set_period_com_amount(total_income, period_id, com_id,
                                                rounder(a + b))
        prior_income = self.data_attachment_points['prior']['income']
        for (acc_id, v0) in prior_income.iteritems():
            for (period_id, v1) in v0.data.iteritems():
                for com_id in v1.iterkeys():
                    a = self._get_period_com_amount(total_income, period_id, com_id)
                    b = self._get_period_com_amount(v0.data, period_id, com_id)
                    self._set_period_com_amount(total_income, period_id, com_id,
                                                rounder(a + b))

        # Calculate total expense
        total_expense = self.total_attachment_points['total_expense'].data = {}
        reconciled_expense = self.data_attachment_points['reconciled']['expense']
        for (acc_id, v0) in reconciled_expense.iteritems():
            for (period_id, v1) in v0.data.iteritems():
                for com_id in v1.iterkeys():
                    a = self._get_period_com_amount(total_expense, period_id, com_id)
                    b = self._get_period_com_amount(v0.data, period_id, com_id)
                    self._set_period_com_amount(total_expense, period_id, com_id,
                                                rounder(a + b))
        unreconciled_expense = self.data_attachment_points['unreconciled']['expense']
        for (acc_id, v0) in unreconciled_expense.iteritems():
            for (period_id, v1) in v0.data.iteritems():
                for com_id in v1.iterkeys():
                    a = self._get_period_com_amount(total_expense, period_id, com_id)
                    b = self._get_period_com_amount(v0.data, period_id, com_id)
                    self._set_period_com_amount(total_expense, period_id, com_id,
                                                rounder(a + b))
        prior_expense = self.data_attachment_points['prior']['expense']
        for (acc_id, v0) in prior_expense.iteritems():
            for (period_id, v1) in v0.data.iteritems():
                for com_id in v1.iterkeys():
                    a = self._get_period_com_amount(total_expense, period_id, com_id)
                    b = self._get_period_com_amount(v0.data, period_id, com_id)
                    self._set_period_com_amount(total_expense, period_id, com_id,
                                                rounder(a + b))

        # Calculate movement
        movement = self.total_attachment_points['movement'].data = {}
        total_income = self.total_attachment_points['total_income'].data
        for (period_id, v1) in total_income.iteritems():
            for com_id in v1.iterkeys():
                a = self._get_period_com_amount(movement, period_id, com_id)
                b = self._get_period_com_amount(total_income, period_id, com_id)
                self._set_period_com_amount(movement, period_id, com_id,
                                            rounder(a + b))
        total_expense = self.total_attachment_points['total_expense'].data
        for (period_id, v1) in total_expense.iteritems():
            for com_id in v1.iterkeys():
                a = self._get_period_com_amount(movement, period_id, com_id)
                b = self._get_period_com_amount(total_expense, period_id, com_id)
                self._set_period_com_amount(movement, period_id, com_id,
                                            rounder(a + b))

    def _set_period_com_amount(self, target_dict, period_id, com_id, amount):
        target_dict.setdefault(period_id, {com_id: [None]}).setdefault(com_id, [None])[0] = amount
    def _get_period_com_amount(self, target_dict, period_id, com_id, default=0.0):
        return target_dict.get(period_id, {com_id: [default]}).get(com_id, [default])[0]

    def sum_up(self, normalizer, rounder, is_zero):
        def upon_entering(node, context):
            node.display_data = {}
            for datum in node.data:
                for (period_id, v1) in datum.data_point.data.iteritems():
                    for com_id in v1.iterkeys():
                        prev = self._get_period_com_amount(node.display_data,
                                                           period_id,
                                                           com_id)
                        val = self._get_period_com_amount(datum.data_point.data,
                                                          period_id,
                                                          com_id)
                        self._set_period_com_amount(node.display_data,
                                                    period_id,
                                                    com_id,
                                                    rounder(prev
                                                            + (datum.multiplier
                                                               * val)))
            context['node'] = node

        def after_each_child(child, context):
            if context['is_total'][0]:
                # We do not sum total node up
                context['is_total'][0] = False
            else:
                for (period_id, v1) in child.display_data.iteritems():
                    for com_id in v1.iterkeys():
                        child_val = self._get_period_com_amount(child.display_data,
                                                                period_id,
                                                                com_id)
                        val = self._get_period_com_amount(context['node'].display_data,
                                                          period_id,
                                                          com_id)
                        self._set_period_com_amount(context['node'].display_data,
                                                    period_id,
                                                    com_id,
                                                    rounder(val
                                                            + child_val))
        def before_leaving(node, context):
            if node.is_total_node():
                context['is_total'][0] = True

        context = {
            'sum': None,
            'is_total': [False],
        }
        via_reporting_tree.tree.traverse(self.tree,
                                         upon_entering_fn=upon_entering,
                                         after_each_child_fn=after_each_child,
                                         before_leaving_fn=before_leaving,
                                         context=context)

    def linearize(self, no_zero):
        def upon_entering(node, context):
            this_row_id = context['row_id'][0]
            context['row_id'][0] += 1

            is_special_node = ((node.id in self.special_nodes_for_fusion)
                               or (node.id in self.special_nodes_for_total))

            data_dict = node.display_data
            if node.is_total_node():
                data_dict = node.total_data[0].data
            for (period_id, v1) in data_dict.iteritems():
                for com_id in v1.iterkeys():
                    amount = self._get_period_com_amount(data_dict,
                                                         period_id,
                                                         com_id)
                    if no_zero and amount == 0.0:
                        continue

                    context['res'].append((this_row_id,
                                           node.id,
                                           period_id,
                                           com_id,
                                           amount,
                                           node.is_leaf(),
                                           node.is_total_node(),
                                           is_special_node))

            if no_zero:
                return

            # Force each tree node to appear in the crosstab
            if ((not node.is_total_node() and len(node.display_data) == 0)
                or (node.is_total_node() and len(node.total_data[0].data) == 0)):
                forcing_com_id = self.company_ids_seen.pop()
                self.company_ids_seen.add(forcing_com_id)
                forcing_period_id = self.period_ids_seen.pop()
                self.period_ids_seen.add(forcing_period_id)

                context['res'].append((this_row_id,
                                       node.id,
                                       forcing_period_id,
                                       forcing_com_id,
                                       None,
                                       node.is_leaf(),
                                       node.is_total_node(),
                                       is_special_node))

        context = {
            'row_id': [0],
            'res': [],
        }
        via_reporting_tree.tree.traverse(self.tree,
                                         upon_entering_fn=upon_entering,
                                         context=context)
        return context['res']

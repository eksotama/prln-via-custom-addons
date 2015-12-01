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

import pooler
from via_reporting_utility.currency import get_currency_toolkit
from via_reporting_utility.pgsql import list_to_pgTable
from via_reporting_utility.pgsql import create_composite_type
from via_reporting_utility.pgsql import create_plpgsql_proc
from via_reporting_utility.company import get_company_ids
from osv import fields, osv
from tools.translate import _
from reporting_service import get_service_name, get_rpt_output
import decimal_precision as dp
from datetime import date
from cash_flow_realization_report_sql import cash_flow_realization_report_sql
from cash_flow_realization_report_sql import def_cash_flow_items_sql
from via_cash_flow_realization_report.cash_flow_tree \
    import tree as cash_flow_tree


class cash_flow_realization_report(osv.osv_memory):
    _name = 'via.cash.flow.realization.report'
    _description = 'VIA Cash Flow Report'
    _rec_name = 'rpt_name'

    _columns = {
        'rpt_name': fields.char('Report name', readonly=True, required=True,
                            size=256),
        'company_id': fields.many2one('res.company', 'Company', required=True,
                                      widget='selection'),
        'currency_id': fields.related('company_id', 'currency_id',
                                      string='Company Currency',
                                      type='many2one', relation='res.currency',
                                      readonly=True),
        'use_indentation': fields.boolean('Indent node name based on depth',
                                          required=True),
        'no_zero': fields.boolean('Exclude node with 0 balance',
                                  required=True),
        'from_date': fields.date('From', required=True),
        'to_date': fields.date('To', required=True),
        'rpt_output': fields.selection(get_rpt_output, 'Output Format',
                                       required=True),
        'tree_id': fields.many2one('via.reporting.tree', 'Reporting Tree',
                                   required=True,
                                   domain=("[('company_id','=',company_id),"
                                           "('tree_type_id.name','=','Cash Flow')]")),

        # The following are internal fields
        'arg': fields.text('Free Argument'),
        'tree_table': fields.text('Tree Table'),
        'report_parameters_table_left': fields.text('Report Parameters Table Right'),
        'report_parameters_table_right': fields.text('Report Parameters Table Left'),
        'decimal_precision': fields.integer('Decimal Precision', required=True,
                                            readonly=True),
    }

    _defaults = {
        'rpt_output': 'pdf',
        'use_indentation': True,
        'decimal_precision': lambda self, cr, uid, ctx: dp.get_precision('Account')(cr)[1],
        'rpt_name': lambda self, cr, uid, ctx: ctx['rpt_name'],
        'from_date': fields.date.context_today,
        'to_date': fields.date.context_today,
        'company_id': lambda self, cr, uid, ctx: self.pool.get('res.users').browse(cr, uid, uid, context=ctx).company_id.id,
        'no_zero': False,
    }

    def _assert_within_fiscalyear(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        fy_pool = self.pool.get('account.fiscalyear')
        fy_ids = fy_pool.search(cr, uid, [('date_start', '<=', obj.from_date),
                                          ('date_stop', '>=', obj.to_date),
                                          ('company_id', '=', obj.company_id.id)],
                                context=context)
        return len(fy_ids) == 1

    _constraints = [
        (_assert_within_fiscalyear,
         'From-date and to-date must be within one fiscal year',
         ['from_date', 'to_date']),
    ]

    def _get_tree_data(self, cr, uid, cid, from_date, to_date, context=None):
        # Get selected company ID and its descendant company IDs
        company = self.pool.get('res.company').browse(cr, uid, cid,
                                                      context=context)
        cids = get_company_ids(company)

        # Get the periods of the selected company
        crit = [('date_stop', '>=', from_date), ('date_start', '<=', to_date),
                ('company_id', '=', cid)]
        period_ids = self.pool.get('account.period').search(cr, uid, crit,
                                                            context=context)
        if not period_ids:
            return []

        periods = self.pool.get('account.period').browse(cr, uid, period_ids,
                                                         context=context)
        period_data = []
        for period in periods:
            period_data.append((period.id, period.date_start, period.date_stop))
        period_data_table = list_to_pgTable(period_data, 'period',
                                            [('id', 'INTEGER'),
                                             ('date_start', 'DATE'),
                                             ('date_stop', 'DATE')])

        acc_ids = self.pool.get('account.account').search(cr, uid,
                                                          [('type', '=', 'liquidity')],
                                                          context=context)

        # Execute query
        query = cash_flow_realization_report_sql() % {
            'ROOT_COMPANY_PERIOD_ID_DATE_START_DATE_STOP_TABLE': period_data_table,
            'FISCAL_YEAR_DATE_START': periods[0].fiscalyear_id.date_start,
            'COMPANY_IDS': ', '.join(str(cid).replace('L', '') for cid in cids),
            'ACCOUNT_IDS': ', '.join('%d' % acc_id for acc_id in acc_ids),
            'DATE_START': from_date,
            'DATE_STOP': to_date,
        }
        cr.execute(query)

        return cr.dictfetchall()

    def _auto_init(self, cr, context=None):
        super(cash_flow_realization_report, self)._auto_init(cr, context=context)
        create_composite_type(cr, 'vcf_tuple',
                              [('id', 'BIGINT'),
                               ('date', 'DATE'),
                               ('type', 'INT'),
                               ('bank_acc_id', 'BIGINT')])
        create_plpgsql_proc(cr, 'cash_flow_items',
                            [('IN', 'date_start', 'DATE'),
                             ('IN', 'date_end', 'DATE'),
                             ('IN', 'company_ids', 'INTEGER[]'),
                             ('IN', 'account_ids', 'INTEGER[]')],
                            'TABLE(type_ CHARACTER VARYING, id_ BIGINT, date_ DATE, bank_acc_id_ BIGINT)',
                            def_cash_flow_items_sql())

    def generate_report(self, cr, uid, ids, context=None):
        # Prepare things
        if type(ids) != list:
            ids = [ids]
        form = self.read(cr, uid, ids, ['use_indentation', 'from_date',
                                        'to_date', 'rpt_output', 'tree_id',
                                        'company_id', 'rpt_name', 'no_zero'],
                         context=context)[0]

        # Get tree data
        tree_data = self._get_tree_data(cr, uid, form['company_id'][0],
                                        form['from_date'], form['to_date'],
                                        context=context)
        if len(tree_data) == 0:
            raise osv.except_osv(_('Error !'),
                                 _('No data to print !'))
        # Now we can assume at least one company exists so that the crosstab
        # can be ensured to display all nodes in the reporting tree.

        # Get reporting tree
        tree = cash_flow_tree(cr, uid, form['tree_id'][0], context=context)

        # Fuse tree data and reporting tree
        form_obj = self.browse(cr, uid, ids, context=context)[0]
        (normalizer,
         rounder,
         is_zero) = get_currency_toolkit(cr, uid, form_obj.currency_id, context)
        tree.attach_data(tree_data, normalizer, rounder, is_zero)

        # Sum the tree up
        tree.sum_up(normalizer, rounder, is_zero)

        # Linearized and stringified the tree
        linearized_tree = tree.linearize(form['no_zero'])
        tree_table = list_to_pgTable(linearized_tree, 'core_data',
                                     [('row_id', 'INTEGER'),
                                      ('node_id', 'INTEGER'),
                                      ('period_id', 'INTEGER'),
                                      ('com_id', 'INTEGER'),
                                      ('amount', 'NUMERIC'),
                                      ('is_leaf', 'BOOLEAN'),
                                      ('is_total_node', 'BOOLEAN'),
                                      ('is_special_node', 'BOOLEAN')])

        # Set report parameters
        report_parameters_left = [(1, 'Report Name', form['rpt_name']),
                                  (2, 'From (YYYY-MM-DD)', form['from_date']),
                                  (3, 'Company', form_obj.company_id.name), ]
        report_parameters_table_left = list_to_pgTable(report_parameters_left,
                                                       't',
                                                       [('ord', 'INTEGER'),
                                                        ('key', 'TEXT'),
                                                        ('value', 'TEXT')])
        report_parameters_right = [(1, 'Reporting Tree', form_obj.tree_id.name),
                                   (2, 'To (YYYY-MM-DD)', form['to_date']), ]
        report_parameters_table_right = list_to_pgTable(report_parameters_right,
                                                       't',
                                                       [('ord', 'INTEGER'),
                                                        ('key', 'TEXT'),
                                                        ('value', 'TEXT')])

        # Memorize the result for parser consumption
        self.write(cr, uid, ids, {
            'tree_table': tree_table,
            'report_parameters_table_left': report_parameters_table_left,
            'report_parameters_table_right': report_parameters_table_right,
        }, context)

        # Redirecting to reporting service
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model',
                                    'via.cash.flow.realization.report')
        data['form'] = form
        return {'type': 'ir.actions.report.xml',
                'report_name': get_service_name(cr,
                                                data['form']['rpt_name'],
                                                data['form']['rpt_output'],
                                                context=context),
                'datas': data}

cash_flow_realization_report()


# The following is to pass the report data to the jasper reports
class ir_actions_report_xml(osv.osv):
    _inherit = 'ir.actions.report.xml'

    def register_all(self, cr):
        rv = super(ir_actions_report_xml, self).register_all(cr)

        cr.execute("SELECT *"
                   " FROM ir_act_report_xml r"
                   "  INNER JOIN ir_model_data d"
                   "   ON r.id = d.res_id"
                   " WHERE d.module = 'via_cash_flow_realization_report'"
                   "  AND d.model = 'ir.actions.report.xml'"
                   " ORDER BY r.id")
        records = cr.dictfetchall()

        class parser(object):
            def __init__(self, cr, uid, ids, data, context):
                _id = data['form']['id']
                pool = pooler.get_pool(cr.dbname).get('via.cash.flow.realization.report')
                o = pool.browse(cr, uid, _id, context)

                self.parameters = {}
                if o.arg is None:
                    self.parameters['ARG'] = ''
                else:
                    self.parameters['ARG'] = o.arg
                self.parameters['TREE_TABLE'] = o.tree_table
                self.parameters['REPORT_PARAMETERS_TABLE_LEFT'] = o.report_parameters_table_left
                self.parameters['REPORT_PARAMETERS_TABLE_RIGHT'] = o.report_parameters_table_right
                self.parameters['REPORT_PARAMETERS_TABLE'] = (o.report_parameters_table_left
                                                              + "," + o.report_parameters_table_right)
                self.parameters['USE_INDENTATION'] = o.use_indentation
                self.parameters['DECIMAL_PRECISION'] = (0
                                                        if o.rpt_output == 'pdf'
                                                        else o.decimal_precision)

            def get(self, key, default):
                if key == 'parameters':
                    return self.parameters
                else:
                    return default

        from jasper_reports.jasper_report import report_jasper

        for record in records:
            name = 'report.%s' % record['report_name']
            report_jasper(name, record['model'], parser)

        return rv

ir_actions_report_xml()

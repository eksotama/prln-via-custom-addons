# -*- encoding: utf-8 -*-
###############################################################################
#
#  Vikasa Infinity Anugrah, PT
#  Copyright (C) 2013 Vikasa Infinity Anugrah <http://www.infi-nity.com>
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

try:
    import release
    from osv import osv, fields
    from tools.translate import _
    from via_jasper_report_utils.framework import register_report_wizard, wizard
except ImportError:
    import openerp
    from openerp import release
    from openerp.osv import osv, fields
    from openerp.tools.translate import _
    from openerp.addons.via_jasper_report_utils.framework import register_report_wizard, wizard

import _financial_reports


RPT_NAME = 'Trial Balance'


class via_jasper_report(osv.osv_memory):
    _inherit = 'via.jasper.report'
    _description = 'Trial Balance'

    _columns = {
        # 'rpt_name': fields.text("Report Name", readonly=True),
        # 'company_ids': fields.many2many('res.company', 'via_report_company_rel',
        #                                 'via_report_id', 'company_id', 'Companies'),
        # 'company_id': fields.many2one('res.company', 'Company'),
        # 'from_mo': fields.selection(_months, 'From'),
        # 'from_yr': fields.selection(_get_year, ''),
        # 'to_mo': fields.selection(_months, 'To'),
        # 'to_yr': fields.selection(_get_year, ''),
        # 'from_dt': fields.date('From'),
        # 'to_dt': fields.date('To'),
        # 'from_dt_2': fields.date('From'),
        # 'to_dt_2': fields.date('To'),
        # 'as_of_dt': fields.date('As of'),
        # 'as_of_yr': fields.selection(_get_year, 'As of Year'),
        # 'rpt_output': fields.selection(utility.get_outputs_selection, 'Output Format',
        #                                required=True),
        # 'orderby_ids': fields.many2many('via.report.orderby', 'via_report_orderby_rel',
        #                                 'via_report_id', 'orderby_id', 'Order By'),
        # 'state': fields.selection(_get_states, 'State'),
        # 'prod_ids': (release.major_version == '6.1'
        #              and fields.many2many('product.product', string='Products')
        #              or fields.many2many('product.product',
        #                                  'via_report_product_rel',
        #                                  'via_report_id',
        #                                  'product_id',
        #                                  string='Products')),
        # 'prod_group_level': fields.integer('Product Grouping Level'),
        # 'prod_ids_2': (release.major_version == '6.1'
        #                and fields.many2many('product.product', string='Products')
        #                or fields.many2many('product.product',
        #                                    'via_report_product_rel_2',
        #                                    'via_report_id',
        #                                    'product_id',
        #                                    string='Products')),
        # 'prod_lot_ids': (release.major_version == '6.1'
        #                  and fields.many2many('stock.production.lot', string='Product Lots')
        #                  or fields.many2many('stock.production.lot',
        #                                      'via_report_production_lot_rel',
        #                                      'via_report_id',
        #                                      'lot_id',
        #                                      string='Product Lots')),
        # 'prod_lot_ids_2': (release.major_version == '6.1'
        #                    and fields.many2many('stock.production.lot', string='Product Lots')
        #                    or fields.many2many('stock.production.lot',
        #                                        'via_report_production_lot_rel_2',
        #                                        'via_report_id',
        #                                        'lot_id',
        #                                        string='Product Lots')),
        # 'reporting_tree_id': fields.many2one('via.reporting.tree', 'Reporting Tree'),
        # 'reporting_tree_node_ids': (release.major_version == '6.1'
        #                             and fields.many2many('via.reporting.tree.node',
        #                                                  string='Reporting Tree Node')
        #                             or fields.many2many('via.reporting.tree.node',
        #                                                 'via_report_reporting_tree_node_rel',
        #                                                 'via_report_id',
        #                                                 'tree_node_id',
        #                                                 string='Reporting Tree Node')),
        # 'analytic_acc_ids': (release.major_version == '6.1'
        #                      and fields.many2many('account.analytic.account',
        #                                           string='Analytic Accounts')
        #                      or fields.many2many('account.analytic.account',
        #                                          'via_report_analytic_acc_rel',
        #                                          'via_report_id',
        #                                          'analytic_acc_id',
        #                                          string='Analytic Accounts')),
        # 'acc_ids': (release.major_version == '6.1'
        #             and fields.many2many('account.account',
        #                                  string='Accounts')
        #             or fields.many2many('account.account',
        #                                 'via_report_acc_rel',
        #                                 'via_report_id',
        #                                 'acc_id',
        #                                 string='Accounts')),
        # 'journal_ids': (release.major_version == '6.1'
        #                 and fields.many2many('account.journal',
        #                                      string='Journals')
        #                 or fields.many2many('account.journal',
        #                                     'via_report_journal_rel',
        #                                     'via_report_id',
        #                                     'journal_id',
        #                                     string='Journals')),
        # 'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year'),
        # 'fiscalyear_id_2': fields.many2one('account.fiscalyear', 'Fiscal Year'),
        # 'target_move': fields.selection([('posted', 'All Posted Entries'),
        #                                  ('all', 'All Entries'),
        #                                  ], 'Target Moves'),
        # 'display_move': fields.boolean('Show Move'),
        # 'use_indentation': fields.boolean('Use Indentation'),
        # 'no_wrap': fields.boolean('No Wrap'),
        # 'display_drcr': fields.boolean('Show Debit & Credit'),
        # 'display_large': fields.boolean('Large Format'),
        # 'reference_label': fields.char('Reference Label', size=128),
        # 'comparison_label': fields.char('Comparison Label', size=128),
        # 'display_comparison': fields.boolean('Enable Comparison'),
        # 'from_period_id': fields.many2one('account.period', 'Start Period'),
        # 'from_period_id_2': fields.many2one('account.period', 'Start Period'),
        # 'to_period_id': fields.many2one('account.period', 'End Period'),
        # 'to_period_id_2': fields.many2one('account.period', 'End Period'),
        # 'date_filter': fields.selection([('filter_no', 'No Filters'),
        #                                  ('filter_date', 'Date'),
        #                                  ('filter_period', 'Periods')], 'Filter By'),
        # 'date_filter_2': fields.selection([('filter_no', 'No Filters'),
        #                                    ('filter_date', 'Date'),
        #                                    ('filter_period', 'Periods')], 'Filter By'),
        # 'location_ids': (release.major_version == '6.1'
        #                  and fields.many2many('stock.location',
        #                                       string='Locations')
        #                  or fields.many2many('stock.location',
        #                                      'via_report_location_rel',
        #                                      'via_report_id',
        #                                      'location_id',
        #                                      string='Locations')),
        # 'salesman_ids': (release.major_version == '6.1'
        #                  and fields.many2many('res.users',
        #                                       string='Salesman')
        #                  or fields.many2many('res.users',
        #                                      'via_report_salesman_rel',
        #                                      'via_report_id',
        #                                      'salesman_id',
        #                                      string='Salesman')),
        # 'customer_ids': (release.major_version == '6.1'
        #                  and fields.many2many('res.partner',
        #                                       string='Customer')
        #                  or fields.many2many('res.partner',
        #                                      'via_report_customer_rel',
        #                                      'via_report_id',
        #                                      'customer_id',
        #                                      string='Customer')),
        # 'customer_addr_ids': (release.major_version == '6.1'
        #                       and fields.many2many('res.partner.address',
        #                                            string='Customer')
        #                       or fields.many2many('res.partner.address',
        #                                           'via_report_customer_addr_rel',
        #                                           'via_report_id',
        #                                           'customer_addr_id',
        #                                           string='Customer')),
        # 'filter_selection': fields.selection(_get_filter_selection,
        #                                      string='Filter By'),
        # 'filter_selection_2': fields.selection(_get_filter_selection_2,
        #                                        string='Filter By'),
        # 'dept_ids': (release.major_version == '6.1'
        #              and fields.many2many('hr.department',
        #                                   string='Departments')
        #              or fields.many2many('hr.department',
        #                                  'via_report_dept_rel',
        #                                  'via_report_id',
        #                                  'dept_id',
        #                                  string='Departments')),
    }

    # DO NOT use the following default dictionary. Use the one in class wizard.
    # The following is presented for your information regarding the system-
    # wide defaults.
    _defaults = {
        # 'rpt_name': lambda self, cr, uid, ctx: ctx.get('via_jasper_report_utils.rpt_name', None),
        # 'from_mo': date.today().month,
        # 'from_yr': date.today().year,
        # 'to_mo': date.today().month,
        # 'to_yr': date.today().year,
        # 'from_dt': str(date.today()),
        # 'to_dt': str(date.today()),
        # 'from_dt_2': str(date.today()),
        # 'to_dt_2': str(date.today()),
        # 'as_of_dt': str(date.today()),
        # 'as_of_yr': date.today().year,
        # 'rpt_output': 'pdf',
        # 'orderby_ids': orderby_get_ids,
        # 'company_id': lambda self, cr, uid, ctx: self.pool.get('res.users').browse(cr, uid, uid, context=ctx).company_id.id,
        # 'prod_group_level': 1,
        # 'fiscalyear_id': default_fiscalyear_id,
        # 'target_move': 'posted',
        # 'date_filter': 'filter_no',
    }

via_jasper_report()


class wizard(_financial_reports.wizard):

    # The structure of _visibility must reflect the placement of the elements.
    # For example, placing 'company_ids' after 'from_dt' will make 'from_dt' be
    # placed on top of 'company_ids'.
    #
    # To have more than one column, simply put the field names in a list.
    # For example, the following structure creates two columns with 'company_ids'
    # located in its own row:
    #     [
    #         'company_ids',
    #         ['from_dt', 'to_dt'],
    #     ]
    #
    # To put a notebook, place the notebook name prefixed by 'notebook:' and put
    # a dictionary at the very end of the row list containing the notebook
    # description such as:
    #     [
    #         'company_ids',
    #         'notebook:notebook_1',
    #         ['from_dt', 'to_dt'],
    #         'notebook:notebook_2',
    #         {
    #             'notebook:notebook_1': [
    #                 ('Accounts', [
    #                     ['fiscalyear_id', 'period_id']
    #                     'acc_ids'
    #                 ])
    #                 ('Journals', [
    #                     'journal_ids'
    #                 ])
    #             ],
    #             'notebook:notebook_2': [
    #                 ('Filters', [
    #                     ['from_dt_2', 'to_dt_2']
    #                     'period_id_2'
    #                 ])
    #                 ('Notes', [
    #                     'notes'
    #                 ])
    #             ],
    #         }
    #     ]
    # A notebook page has a name in the form of: notebook_name + '_' + page_idx.
    #
    # To put a separator, place the separator name prefixed by 'separator:'.
    #
    # The element to select the report output format has the name 'rpt_output'.
    # By default, it is located at the very end in its own row before the buttons
    # to print or cancel printing.
    #
    _visibility = [
        ['company_id', 'reporting_tree_id'],
        ['fiscalyear_id', 'target_move'],
        'use_indentation',
        'no_wrap',
        ['as_of_dt'],
        ['rpt_output', 'display_large'],
        ['reference_label', 'display_comparison'],
        'notebook:first_notebook',

        # Optional references
        {
            'notebook:first_notebook': [
                ('Filters', [
                    'date_filter',
                    'separator:Dates',
                    'from_dt',
                    'to_dt',
                    'separator:Periods',
                    'from_period_id',
                    'to_period_id',
                ]),
                ('Journals', [
                    'journal_ids',
                ]),
                ('Accounts', [
                    'acc_ids',
                ]),
                ('Comparison', [
                    ['comparison_label', 'fiscalyear_id_2'],
                    'date_filter_2',
                    'separator:Dates',
                    'from_dt_2',
                    'to_dt_2',
                    'separator:Periods',
                    'from_period_id_2',
                    'to_period_id_2',
                ]),
            ]
        }
    ]

    # Override this method to return a tuple (callable, context) used to filter
    # a list of report service names that are available under a particular
    # report name (e.g., RPT_NAME + ' (By Value)' has rpt_a4_portrait,
    # rpt_a4_landscape, and rpt_a3_landscape). The callable must have the
    # following signature:
    #     lambda service_names, context
    #
    # Later on the callable will be given a list of report service names in
    # service_names and a context that is found in the tuple (callable,
    # context) in context (i.e., the context in the tuple is prepared in this
    # method to provide information needed by the callable).
    #
    # The callable must then return just a single report service name.
    #
    def get_service_name_filter(self, cr, uid, form, context=None):
        def service_name_filter(service_names, context):
            names = filter(lambda nm: nm.find('trial_balance_') == 0,
                           service_names)
            if form.rpt_output != 'pdf':
                return names

            if form.display_large:
                return filter(lambda nm: nm.find('_a3_landscape') != -1, names)
            else:
                return filter(lambda nm: nm.find('_a3_landscape') == -1, names)
        return (service_name_filter, context)

register_report_wizard(RPT_NAME, wizard)

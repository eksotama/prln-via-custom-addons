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
    from via_reporting_utility.pgsql import create_composite_type
    from via_reporting_utility.pgsql import create_aggregator
    from via_reporting_utility.pgsql import create_plpgsql_proc
except ImportError:
    import openerp
    from openerp import release
    from openerp.osv import osv, fields
    from openerp.tools.translate import _
    from openerp.addons.via_jasper_report_utils.framework import register_report_wizard, wizard
    from openerp.addons.via_reporting_utility.pgsql import create_composite_type
    from openerp.addons.via_reporting_utility.pgsql import create_aggregator
    from openerp.addons.via_reporting_utility.pgsql import create_plpgsql_proc

import _financial_reports
from copy import deepcopy


RPT_NAME = 'General Ledger'



class tree_node(osv.osv):
    _inherit = 'via.reporting.tree.node'
    _columns = {
        # Formatting attributes
        'move_bold': fields.boolean('Bold'),
        'move_italic': fields.boolean('Italic'),
        'move_underline': fields.boolean('Underline'),
    }
tree_node()


_GL_ARRAY_CAT_DEF = '''
DECLARE
    array_1_ BIGINT[];
    array_2_ BIGINT[];
BEGIN
    IF array_1 IS NULL THEN
        array_1_ := ARRAY[]::BIGINT[];
    ELSE
        array_1_ := array_1;
    END IF;
    IF array_2 IS NULL THEN
        array_2_ := ARRAY[]::BIGINT[];
    ELSE
        array_2_ := array_2;
    END IF;
    RETURN array_1_ || array_2_;
END
'''

_GL_DECORATOR_DEF = '''
DECLARE
    top_company_com_order BIGINT := (SELECT MIN(com_order)
                                     FROM UNNEST(axes_data_points));

    rtn_rec RECORD;
    header_rec GL_AXES_DATA_POINT;
    body_rec GL_AXES_DATA_POINT;
    footer_rec GL_AXES_DATA_POINT;

    gl_journal_item_nth_row_dict GL_ID_NTH_ROW[];
    ji_rec RECORD;
    ji_start BOOLEAN;

    nth BIGINT;
    record_to_return GL_DECORATED_RECORD;
BEGIN
    nth := 0;

    FOR rtn_rec IN (SELECT DISTINCT rtn_order
                    FROM UNNEST(axes_data_points)
                    ORDER BY
                     rtn_order) LOOP

        -- HEADER
        nth := nth + 1;
        FOR header_rec IN (SELECT *
                           FROM UNNEST(axes_data_points)
                           WHERE rtn_order = rtn_rec.rtn_order
                           ORDER BY com_order, comparison_order) LOOP
            IF header_rec.move_lines_count IS NULL
               OR header_rec.decorator_blank_line THEN
                record_to_return := (CASE WHEN header_rec.decorator_blank_line THEN NULL ELSE 1 END,
                                     NULL,
                                     header_rec.decorator_bold,
                                     header_rec.decorator_underline,
                                     header_rec.decorator_italic,
                                     header_rec.decorator_move_bold,
                                     header_rec.decorator_move_underline,
                                     header_rec.decorator_move_italic,
                                     header_rec.decorator_blank_line,
                                     header_rec.decorator_title_line,
                                     nth,
                                     header_rec.comparison_order,
                                     header_rec.comparison_label,
                                     header_rec.com_order,
                                     header_rec.com_name,
                                     header_rec.rtn_name,
                                     header_rec.rtn_level,
                                     NULL,
                                     NULL,
                                     NULL,
                                     NULL,
                                     NULL,
                                     NULL,
                                     NULL,
                                     NULL,
                                     NULL)::GL_DECORATED_RECORD;
                RETURN NEXT record_to_return;
                CONTINUE;
            END IF;
            record_to_return := (1,
                                 CASE WHEN header_rec.decorator_title_line THEN NULL ELSE 1 END,
                                 header_rec.decorator_bold,
                                 header_rec.decorator_underline,
                                 header_rec.decorator_italic,
                                 header_rec.decorator_move_bold,
                                 header_rec.decorator_move_underline,
                                 header_rec.decorator_move_italic,
                                 header_rec.decorator_blank_line,
                                 header_rec.decorator_title_line,
                                 nth,
                                 header_rec.comparison_order,
                                 header_rec.comparison_label,
                                 header_rec.com_order,
                                 header_rec.com_name,
                                 header_rec.rtn_name,
                                 header_rec.rtn_level,
                                 header_rec.bb,
                                 header_rec.dr,
                                 header_rec.cr,
                                 header_rec.mv,
                                 header_rec.eb,
                                 NULL,
                                 NULL,
                                 NULL,
                                 NULL)::GL_DECORATED_RECORD;
            RETURN NEXT record_to_return;
        END LOOP;
        -- HEADER [END]

        -- MOVE DATA
        gl_journal_item_nth_row_dict := ARRAY[]::GL_ID_NTH_ROW[];
        FOR body_rec IN (SELECT *
                         FROM UNNEST(axes_data_points)
                         WHERE rtn_order = rtn_rec.rtn_order
                         ORDER BY com_order, comparison_order) LOOP

            IF body_rec.move_lines_count IS NULL
               OR body_rec.decorator_blank_line THEN
                CONTINUE;
            END IF;

            record_to_return := (NULL,
                                 NULL,
                                 body_rec.decorator_bold,
                                 body_rec.decorator_underline,
                                 body_rec.decorator_italic,
                                 body_rec.decorator_move_bold,
                                 body_rec.decorator_move_underline,
                                 body_rec.decorator_move_italic,
                                 body_rec.decorator_blank_line,
                                 body_rec.decorator_title_line,
                                 NULL,
                                 body_rec.comparison_order,
                                 body_rec.comparison_label,
                                 body_rec.com_order,
                                 body_rec.com_name,
                                 body_rec.rtn_name,
                                 body_rec.rtn_level,
                                 body_rec.bb,
                                 body_rec.dr,
                                 body_rec.cr,
                                 body_rec.mv,
                                 CASE WHEN body_rec.decorator_title_line THEN body_rec.eb ELSE body_rec.bb END,
                                 NULL,
                                 NULL,
                                 NULL,
                                 NULL)::GL_DECORATED_RECORD;

            ji_start := TRUE;
            FOR ji_rec IN (SELECT nth_dict.nth_row AS this_nth, ji.*
                           FROM UNNEST(body_rec.move_lines) ji_id
                            INNER JOIN UNNEST(journal_items) ji
                             ON (ji_id = ji.id
                                 AND body_rec.comparison_order = ji.comparison_order)
                            LEFT JOIN (SELECT DISTINCT *
                                       FROM UNNEST(gl_journal_item_nth_row_dict)) nth_dict
                             ON (nth_dict.comparison_order,
                                 nth_dict.id) = (body_rec.comparison_order,
                                                 ji_id)
                           WHERE
                            body_rec.move_lines_count > 0
                           ORDER BY
                            ji.date,
                            ji.no) LOOP

                IF ji_start THEN
                    ji_start := FALSE;
                ELSE
                    RETURN NEXT record_to_return;
                END IF;

                IF body_rec.com_order = top_company_com_order THEN
                    nth := nth + 1;
                    record_to_return.nth_row := nth;
                ELSE
                    IF ji_rec.this_nth IS NULL THEN
                        nth := nth + 1;
                        record_to_return.nth_row := nth;
                    ELSE
                        record_to_return.nth_row := ji_rec.this_nth;
                    END IF;
                END IF;
                record_to_return.decorator_header_band_selector := 3;
                IF record_to_return.decorator_title_line THEN
                    record_to_return.decorator_band_selector := 2;
                    record_to_return.mv := (ji_rec.top_level_debit - ji_rec.top_level_credit);
                ELSE
                    record_to_return.decorator_band_selector := 6;
                    record_to_return.eb := (record_to_return.eb
                                            + (ji_rec.top_level_debit - ji_rec.top_level_credit));
                END IF;
                record_to_return.ji_date := ji_rec.date;
                record_to_return.ji_no := ji_rec.no;
                record_to_return.ji_partner := ji_rec.partner;
                record_to_return.ji_remarks := ji_rec.remarks;
                record_to_return.dr := ji_rec.top_level_debit;
                record_to_return.cr := ji_rec.top_level_credit;

                IF body_rec.com_order = top_company_com_order THEN
                    gl_journal_item_nth_row_dict := (gl_journal_item_nth_row_dict
                                                     || (body_rec.comparison_order, ji_rec.id, nth)::GL_ID_NTH_ROW);
                END IF;
            END LOOP;

            -- Last move line
            IF NOT ji_start THEN
                IF NOT record_to_return.decorator_title_line THEN
                    record_to_return.decorator_band_selector := 3;
                END IF;
                RETURN NEXT record_to_return;
            END IF;
            -- Last move line [END]

        END LOOP;
        -- MOVE_DATA [END]

        -- FOOTER
        nth := nth + 1;
        FOR footer_rec IN (SELECT *
                            FROM UNNEST(axes_data_points)
                            WHERE rtn_order = rtn_rec.rtn_order
                            ORDER BY com_order, comparison_order) LOOP

            IF footer_rec.move_lines_count IS NULL
               OR footer_rec.decorator_blank_line
               OR footer_rec.decorator_title_line THEN
                CONTINUE;
            END IF;

            IF footer_rec.move_lines_count = 0 OR ARRAY_LENGTH(journal_items, 1) IS NULL THEN
                record_to_return := (2,
                                     2,
                                     footer_rec.decorator_bold,
                                     footer_rec.decorator_underline,
                                     footer_rec.decorator_italic,
                                     footer_rec.decorator_move_bold,
                                     footer_rec.decorator_move_underline,
                                     footer_rec.decorator_move_italic,
                                     footer_rec.decorator_blank_line,
                                     footer_rec.decorator_title_line,
                                     nth,
                                     footer_rec.comparison_order,
                                     footer_rec.comparison_label,
                                     footer_rec.com_order,
                                     footer_rec.com_name,
                                     footer_rec.rtn_name,
                                     footer_rec.rtn_level,
                                     footer_rec.bb,
                                     footer_rec.dr,
                                     footer_rec.cr,
                                     footer_rec.mv,
                                     footer_rec.eb,
                                     NULL,
                                     NULL,
                                     NULL,
                                     NULL)::GL_DECORATED_RECORD;
                RETURN NEXT record_to_return;

                record_to_return.nth_row := nth + 1;
                record_to_return.decorator_header_band_selector := NULL;
                record_to_return.decorator_band_selector := 5;
                RETURN NEXT record_to_return;

            ELSE
                record_to_return := (2,
                                     4,
                                     footer_rec.decorator_bold,
                                     footer_rec.decorator_underline,
                                     footer_rec.decorator_italic,
                                     footer_rec.decorator_move_bold,
                                     footer_rec.decorator_move_underline,
                                     footer_rec.decorator_move_italic,
                                     footer_rec.decorator_blank_line,
                                     footer_rec.decorator_title_line,
                                     nth,
                                     footer_rec.comparison_order,
                                     footer_rec.comparison_label,
                                     footer_rec.com_order,
                                     footer_rec.com_name,
                                     footer_rec.rtn_name,
                                     footer_rec.rtn_level,
                                     footer_rec.bb,
                                     footer_rec.dr,
                                     footer_rec.cr,
                                     footer_rec.mv,
                                     footer_rec.eb,
                                     NULL,
                                     NULL,
                                     NULL,
                                     NULL)::GL_DECORATED_RECORD;
                RETURN NEXT record_to_return;
            END IF;

        END LOOP;
        nth := nth + 1;
        -- FOOTER [END]

    END LOOP;
END
'''

class via_jasper_report(osv.osv_memory):
    def _auto_init(self, cr, context=None):
        super(via_jasper_report, self)._auto_init(cr, context=context)
        create_plpgsql_proc(cr, 'gl_array_cat',
                            [('IN', 'array_1', 'BIGINT[]'),
                             ('IN', 'array_2', 'BIGINT[]')],
                            'BIGINT[]',
                            _GL_ARRAY_CAT_DEF)
        create_aggregator(cr, 'gl_array_reduce', 'BIGINT[]',
                          {'sfunc': 'gl_array_cat',
                           'stype': 'BIGINT[]'})
        create_composite_type(cr, 'gl_journal_item',
                              [('id', 'BIGINT'),
                               ('date', 'DATE'),
                               ('no', 'VARCHAR'),
                               ('partner', 'VARCHAR'),
                               ('remarks', 'VARCHAR'),
                               ('debit', 'NUMERIC'),
                               ('credit', 'NUMERIC'),
                               ('top_level_debit', 'NUMERIC'),
                               ('top_level_credit', 'NUMERIC'),
                               ('comparison_order', 'BIGINT'),
                               ('com_id', 'BIGINT')])
        create_composite_type(cr, 'gl_axes_data_point',
                              [('decorator_bold', 'BOOLEAN'),
                               ('decorator_underline', 'BOOLEAN'),
                               ('decorator_italic', 'BOOLEAN'),
                               ('decorator_move_bold', 'BOOLEAN'),
                               ('decorator_move_underline', 'BOOLEAN'),
                               ('decorator_move_italic', 'BOOLEAN'),
                               ('decorator_blank_line', 'BOOLEAN'),
                               ('decorator_title_line', 'BOOLEAN'),
                               ('rtn_order', 'BIGINT'),
                               ('comparison_order', 'BIGINT'),
                               ('comparison_label', 'VARCHAR'),
                               ('com_order', 'BIGINT'),
                               ('com_id', 'BIGINT'),
                               ('com_name', 'VARCHAR'),
                               ('rtn_name', 'VARCHAR'),
                               ('rtn_level', 'BIGINT'),
                               ('bb', 'NUMERIC'),
                               ('dr', 'NUMERIC'),
                               ('cr', 'NUMERIC'),
                               ('mv', 'NUMERIC'),
                               ('eb', 'NUMERIC'),
                               ('move_lines_count', 'NUMERIC'),
                               ('move_lines', 'BIGINT[]')])
        create_composite_type(cr, 'gl_decorated_record',
                              [('decorator_header_band_selector', 'INT'),
                               ('decorator_band_selector', 'INT'),
                               ('decorator_bold', 'BOOLEAN'),
                               ('decorator_underline', 'BOOLEAN'),
                               ('decorator_italic', 'BOOLEAN'),
                               ('decorator_move_bold', 'BOOLEAN'),
                               ('decorator_move_underline', 'BOOLEAN'),
                               ('decorator_move_italic', 'BOOLEAN'),
                               ('decorator_blank_line', 'BOOLEAN'),
                               ('decorator_title_line', 'BOOLEAN'),
                               ('nth_row', 'BIGINT'),
                               ('comparison_order', 'BIGINT'),
                               ('comparison_label', 'VARCHAR'),
                               ('com_order', 'BIGINT'),
                               ('com_name', 'VARCHAR'),
                               ('rtn_name', 'VARCHAR'),
                               ('rtn_level', 'BIGINT'),
                               ('bb', 'NUMERIC'),
                               ('dr', 'NUMERIC'),
                               ('cr', 'NUMERIC'),
                               ('mv', 'NUMERIC'),
                               ('eb', 'NUMERIC'),
                               ('ji_date', 'DATE'),
                               ('ji_no', 'VARCHAR'),
                               ('ji_partner', 'VARCHAR'),
                               ('ji_remarks', 'VARCHAR')])
        create_composite_type(cr, 'gl_id_nth_row',
                              [('comparison_order', 'BIGINT'),
                               ('id', 'BIGINT'),
                               ('nth_row', 'BIGINT')])
        create_plpgsql_proc(cr, 'gl_decorator',
                            [('IN', 'axes_data_points', 'GL_AXES_DATA_POINT[]'),
                             ('IN', 'journal_items', 'GL_JOURNAL_ITEM[]')],
                            'SETOF GL_DECORATED_RECORD',
                            _GL_DECORATOR_DEF)

    _inherit = 'via.jasper.report'
    _description = 'General Ledger'

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
        ['use_indentation', 'display_move'],
        ['no_wrap', 'display_drcr'],
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

    # The values in the dictionary below must be callables with signature:
    #     lambda self, cr, uid, context
    _defaults = deepcopy(_financial_reports.wizard._defaults)
    _defaults.update({
        'display_move': lambda self, cr, uid, context: True,
    })

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
            names = filter(lambda nm: nm.find('general_ledger_') == 0,
                           service_names)
            if form.rpt_output != 'pdf':
                return names

            if form.display_large:
                return filter(lambda nm: nm.find('_a3_landscape') != -1, names)
            else:
                return filter(lambda nm: nm.find('_a3_landscape') == -1, names)
        return (service_name_filter, context)

register_report_wizard(RPT_NAME, wizard)

# -*- encoding: utf-8 -*-
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

MODULE_NAME = 'via_jasper_report_utils'
VIEW_NAME = 'via_jasper_report_main_form_view'

try:
    import release
    import pooler
    from osv import osv, fields, orm
    if release.major_version == '6.1':
        import openerp.modules as addons
    else:
        import addons
    from via_jasper_report_utils import utility
    from tools.translate import _
    from tools import DEFAULT_SERVER_DATE_FORMAT
except ImportError:
    import openerp
    from openerp import release
    from openerp import pooler
    from openerp.osv import osv, fields, orm
    import openerp.modules as addons
    from openerp.addons.via_jasper_report_utils import utility
    from openerp.tools.translate import _
    from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

import calendar
from lxml import etree
import re
import os
import glob
from datetime import date
from datetime import datetime


_marshalled_data_registry = {}
_report_wizard_registry = {}


def normalize_rpt_name(rpt_name):
    return ''.join(map(lambda c: c.lower(),
                       filter(lambda c: c.isalpha(),
                              rpt_name)))


def register_report_wizard(rpt_name, wizard_class):
    normalized_rpt_name = normalize_rpt_name(rpt_name)
    if normalized_rpt_name in _report_wizard_registry:
        raise Exception('Report "%s" already registered its wizard'
                        % normalized_rpt_name)
    _report_wizard_registry.update({normalized_rpt_name: wizard_class})


class wizard(object):
    _onchange = {}
    _visibility = []
    _required = ['rpt_output']
    _readonly = []
    _attrs = {}
    _domain = {
        'fiscalyear_id': "[('company_id','=',company_id)]",
        'from_period_id': "[('fiscalyear_id','=',fiscalyear_id)]",
        'to_period_id': "[('fiscalyear_id','=',fiscalyear_id)]",
        'prod_ids': "[('product_tmpl_id.company_id','=',False)]",
        'prod_ids_2': "[('product_tmpl_id.company_id','=',False)]",
        'prod_lot_ids': "[('product_id.product_tmpl_id.company_id','=',False)]",
        'prod_lot_ids_2': "[('product_id.product_tmpl_id.company_id','=',False)]",
        'reporting_tree_id': "[('company_id','=',False)]",
        'reporting_tree_node_ids': "[('tree_id','=',reporting_tree_id),('children','=',False)]",
        'analytic_acc_ids': "[('company_id','=',False)]",
        'acc_ids': "[('company_id','=',False)]",
        'journal_ids': "[('company_id','=',False)]",
        'fiscalyear_id_2': "[('company_id','=',company_id)]",
        'from_period_id_2': "[('fiscalyear_id','=',fiscalyear_id_2)]",
        'to_period_id_2': "[('fiscalyear_id','=',fiscalyear_id_2)]",
        'location_ids': "[('company_id','=',False),('usage','=','internal')]",
        'salesman_ids': "[('company_id','=',False)]",
        'customer_ids': "[('company_id','=',False),('customer','=',True)]",
        'dept_ids': "[('company_id','=',False)]",
    }
    if float(release.major_version) < 7.0:
        _domain.update({
            'customer_addr_ids': "[('company_id','=',False),('partner_id.customer','=',True)]",
        })

    _label = {}

    _defaults = {}

    _selections = {}

    _tree_columns = {
        'company_ids': ['name'],
        'prod_ids': ['default_code', 'name_template'],
        'prod_ids_2': ['default_code', 'name_template'],
        'prod_lot_ids': ['name'],
        'prod_lot_ids_2': ['name'],
        'reporting_tree_node_ids': ['name'],
        'location_ids': ['name'],
        'salesman_ids': ['name'],
        'customer_ids': ['name'],
    }
    if float(release.major_version) < 7.0:
        _tree_columns.update({
            'customer_addr_ids': ['partner_id', 'state_id'],
        })

    def __init__(self, cr):
        self.pool = pooler.get_pool(cr.dbname)

    def get_service_name_filter(self, cr, uid, form, context=None):
        return (lambda service_names, ctx: service_names, context)


class OerpViewArch(object):
    # Currently no row span is handled
    def __init__(self, rows, string=None, name=None):
        self.string = string
        self.name = name
        self._count_col(rows)
        if isinstance(rows[-1], dict):
            self._rows = rows[:-1]
            self._resolve_references(rows[-1])
        else:
            self._rows = rows

    def _resolve_references(self, references):

        def _resolve_notebook(name, val):
            res = []
            for (idx, entry) in enumerate(val):
                res.append(OerpViewArch(entry[1],
                                        string=entry[0],
                                        name='%s_%d' % (name, idx)))
            return res

        reference_keys = [('notebook:', _resolve_notebook)]

        for ref, val in references.iteritems():
            for (ref_key, resolve) in reference_keys:
                if ref.find(ref_key) == 0:
                    res = resolve(ref[len(ref_key):], val)
                    self.__setattr__(ref[len(ref_key):], res)
                    return
            raise Exception('Unknown view references "%s"' % ref)

    def arch(self, parent_element=None):
        if parent_element is None:
            self._arch = etree.Element('form',
                                       col=self._int(self._col_count),
                                       string=(self.string or ''))
        else:
            self._arch = parent_element

        for row in self._rows:
            self._create_row(row, self._col_count)

        return self._arch

    def _count_col(self, rows):
        for row in rows:
            if not isinstance(row, list):
                self._col_count = max(getattr(self, '_col_count', 0), 1)
            else:
                self._count_col_in_a_row(row)

    def _count_col_in_a_row(self, row):
        col_count = 0
        for col in row:
            if not isinstance(col, list):
                col_count += 1
            else:
                pass # No row span is handled for now
        self._col_count = max(getattr(self, '_col_count', 0), col_count)

    def _create_row(self, row, colspan):
        if not isinstance(row, list):
            self._create_element(row, 1, colspan)
        else:
            self._create_col(row, 1)
            self._create_element('newline', 1, colspan)

    def _create_col(self, row, rowspan):
        for col in row:
            if not isinstance(col, list):
                self._create_element(col, rowspan, 1)
            else:
                pass # No row span is handled for now

    def _int(self, colspan):
        return '%d' % (colspan * 2)

    def _create_element(self, name, rowspan, colspan):
        if name is None:
            etree.SubElement(self._arch, 'label',
                             colspan=self._int(colspan))
        elif name == 'newline':
            etree.SubElement(self._arch, 'newline')
        elif name.find('notebook:') == 0:
            notebook = etree.SubElement(self._arch, 'notebook',
                                        colspan=self._int(colspan))
            for spec in getattr(self, name[len('notebook:'):]):
                page = etree.SubElement(notebook, 'page',
                                        string=spec.string,
                                        name=spec.name)
                container = etree.SubElement(page, 'group',
                                             col=self._int(spec._col_count))
                spec.arch(container)
        elif name.find('separator:') == 0:
            separator = etree.SubElement(self._arch, 'separator',
                                         colspan=self._int(colspan),
                                         string=name[len('separator:'):])
        else:
            etree.SubElement(self._arch, 'field',
                             name=name,
                             colspan=self._int(colspan))

def dt(date_string):
    return datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()

class via_jasper_report(osv.osv_memory):
    _name = "via.jasper.report"
    _description = 'Standard VIA wizard for generating Jasper Reports'

    _jasper_report_indicator = 'jasper_report = True'
    _report_table = 'ir_act_report_xml'

    def __getattribute__(self, name):
        if name.find('onchange_') == 0:
            normalized_rpt_name, field_name = name.split('_', 2)[1:]
            return _report_wizard_registry[normalized_rpt_name]._onchange[field_name][0]
        return super(via_jasper_report, self).__getattribute__(name)

    def tree_columns_create_view(self, cr, uid, field, rpt_name, tree_columns):
        report_dir_name = ''.join(map(lambda c: c == ' ' and '_' or c.lower(),
                                      ' '.join(filter(lambda w: len(w) > 0,
                                                      filter(lambda c: c.isalnum() or c == ' ',
                                                             ''.join(map(lambda c: c.isalnum() and c or ' ',
                                                                         rpt_name))).split(' ')))))
        uid = 1 # Creating a tree view is an internal logic that should work for everyone
        xml_id = (''.join(part[0] for part in report_dir_name.split('_'))
                  + '_' + field + '_tree_columns')
        model = self._columns[field]._obj

        imd_pool = self.pool.get('ir.model.data')
        imd_ids = imd_pool.search(cr, uid, [('name','=',xml_id),
                                            ('module','=',MODULE_NAME)])
        if len(imd_ids):
            existing_tree_view = imd_pool.get_object(cr, uid, MODULE_NAME, xml_id)
        else:
            existing_tree_view = None

        model_pool = self.pool.get(model)
        model_tree_view = model_pool.fields_view_get(cr, uid,
                                                     view_type='tree')
        tree_str = etree.XML(model_tree_view['arch']).get('string', '')
        tree_field_names = set(model_tree_view['fields'].keys())

        tree_el = etree.Element('tree', string=tree_str)
        for col_name in tree_columns:
            etree.SubElement(tree_el, 'field', name=col_name)
            try:
                tree_field_names.remove(col_name)
            except KeyError:
                pass
        for tree_field_name in tree_field_names:
            etree.SubElement(tree_el, 'field', name=tree_field_name,
                             invisible='1')
        arch = etree.tostring(tree_el, pretty_print=True)

        if existing_tree_view:
            if existing_tree_view.arch == arch:
                pass
            else:
                existing_tree_view.write({'arch': arch})
        else:
            res_id = imd_pool._update(cr, uid, 'ir.ui.view', MODULE_NAME, {
                'name': xml_id,
                'model': model,
                'type': 'tree',
                'arch': arch,
            }, xml_id=xml_id, mode='update')

        return MODULE_NAME + '.' + xml_id

    _default_view_arch_updated = False

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):

        if context is None:
            context = {}

        result = super(via_jasper_report, self).fields_view_get(cr, uid, view_id,
                                                                view_type, context=context,
                                                                toolbar=toolbar,
                                                                submenu=submenu)

        _report_name = context.get('via_jasper_report_utils.rpt_name', '')
        if not _report_name:
            return result

        normalized_rpt_name = normalize_rpt_name(_report_name)
        wizard_class = _report_wizard_registry[normalized_rpt_name]

        _arch = OerpViewArch(wizard_class._visibility,
                             string='VIA Jasper Report Wizard').arch()
        if not _arch.xpath('//field[@name="rpt_output"]'):
            etree.SubElement(_arch, 'field',
                             name='rpt_output', colspan=_arch.get('col'))
        wizard_buttons_group = etree.SubElement(_arch, 'group',
                                                name='wizard_buttons',
                                                colspan=_arch.get('col'),
                                                col='2')
        etree.SubElement(wizard_buttons_group, 'button',
                         icon='gtk-cancel',
                         special='cancel',
                         string='Cancel')
        etree.SubElement(wizard_buttons_group, 'button',
                         name='print_report',
                         icon='gtk-print',
                         type='object',
                         string='Print',
                         default_focus='1')

        for _field in _arch.xpath('//field'):
            field_name = _field.get('name')
            if field_name in (wizard._required + wizard_class._required):
                _field.set('required', '1')
            if field_name in wizard_class._readonly:
                _field.set('readonly', '1')
            if field_name in wizard_class._onchange:
                args = wizard_class._onchange[field_name][1:]
                _field.set('on_change',
                           'onchange_%s_%s(%s)'
                           % (normalized_rpt_name,
                              field_name,
                              ', '.join(args)))
            if field_name in wizard_class._attrs:
                _field.set('attrs', wizard_class._attrs[field_name])
            _domain = wizard._domain
            _domain.update(wizard_class._domain)
            if field_name in _domain:
                _field.set('domain', _domain[field_name])
            if field_name in wizard_class._label:
                _field.set('string', wizard_class._label[field_name])
            _tree_columns = wizard._tree_columns
            _tree_columns.update(wizard_class._tree_columns)
            if field_name in _tree_columns:
                tree_view_ref = self.tree_columns_create_view(cr, uid, field_name,
                                                              _report_name,
                                                              _tree_columns[field_name])
                _field.set('context', str({'tree_view_ref': tree_view_ref}))

        for _page in _arch.xpath('//page'):
            page_name = _page.get('name')

            if page_name in wizard_class._attrs:
                _page.set('attrs', wizard_class._attrs[page_name])

        if float(release.major_version) >= 6.1:
            for element in _arch.xpath('//*'):
                orm.setup_modifiers(element, context=context)

        result['arch'] = etree.tostring(_arch)
        return result

    def _get_year(self, cr, uid, context=None):
        return tuple([(year, year) for year in range(1970,
                                                     date.today().year + 1)])

    def _get_states(self, cr, uid, context=None):
        if context is None:
            context = {}
        rpt_name = context.get('via_jasper_report_utils.rpt_name', False)
        return rpt_name and getattr(_report_wizard_registry[normalize_rpt_name(rpt_name)],
                                    '_selections', {}).get('state', []) or []

    def _get_filter_selection(self, cr, uid, context=None):
        if context is None:
            context = {}
        rpt_name = context.get('via_jasper_report_utils.rpt_name', False)
        return rpt_name and getattr(_report_wizard_registry[normalize_rpt_name(rpt_name)],
                                    '_selections', {}).get('filter_selection', []) or []

    def _get_filter_selection_2(self, cr, uid, context=None):
        if context is None:
            context = {}
        rpt_name = context.get('via_jasper_report_utils.rpt_name', False)
        return rpt_name and getattr(_report_wizard_registry[normalize_rpt_name(rpt_name)],
                                    '_selections', {}).get('filter_selection_2', []) or []

    _months = [(1, 'January'), (2, 'February'), (3, 'March'),
               (4, 'April'), (5, 'May'), (6, 'June'), (7, 'July'),
               (8, 'August'), (9, 'September'), (10, 'October'),
               (11, 'November'), (12, 'December')]

    def orderby_get_ids(self, cr, uid, context=None):
        rpt_name = context.get('via_jasper_report_utils.rpt_name', '')
        return rpt_name and self.pool.get('via.report.orderby').orderby_get_ids(cr, uid, normalize_rpt_name(rpt_name), context=context) or []

    _columns = {
        'rpt_name': fields.text("Report Name", readonly=True),
        'company_ids': fields.many2many('res.company', 'via_report_company_rel',
                                        'via_report_id', 'company_id', 'Companies'),
        'company_id': fields.many2one('res.company', 'Company'),
        'from_mo': fields.selection(_months, 'From'),
        'from_yr': fields.selection(_get_year, ''),
        'to_mo': fields.selection(_months, 'To'),
        'to_yr': fields.selection(_get_year, ''),
        'from_dt': fields.date('From'),
        'to_dt': fields.date('To'),
        'from_dt_2': fields.date('From'),
        'to_dt_2': fields.date('To'),
        'as_of_dt': fields.date('As of'),
        'as_of_yr': fields.selection(_get_year, 'As of Year'),
        'rpt_output': fields.selection(utility.get_outputs_selection, 'Output Format',
                                       required=True),
        'orderby_ids': fields.many2many('via.report.orderby', 'via_report_orderby_rel',
                                        'via_report_id', 'orderby_id', 'Order By'),
        'state': fields.selection(_get_states, 'State'),
        'prod_ids': fields.many2many('product.product',
                                     'via_report_product_rel',
                                     'via_report_id',
                                     'product_id',
                                     string='Products'),
        'prod_ids_empty_is_none': fields.boolean('Products When Empty Means None'),
        'prod_group_level': fields.integer('Product Grouping Level'),
        'prod_ids_2': fields.many2many('product.product',
                                       'via_report_product_rel_2',
                                       'via_report_id',
                                       'product_id',
                                       string='Products'),
        'prod_ids_2_empty_is_none': fields.boolean('Products When Empty Means None'),
        'prod_lot_ids': fields.many2many('stock.production.lot',
                                         'via_report_production_lot_rel',
                                         'via_report_id',
                                         'lot_id',
                                         string='Product Lots'),
        'prod_lot_ids_empty_is_none': fields.boolean('Product Lots When Empty Means None'),
        'prod_lot_ids_2': fields.many2many('stock.production.lot',
                                           'via_report_production_lot_rel_2',
                                           'via_report_id',
                                           'lot_id',
                                           string='Product Lots'),
        'prod_lot_ids_2_empty_is_none': fields.boolean('Product Lots When Empty Means None'),
        'reporting_tree_id': fields.many2one('via.reporting.tree', 'Reporting Tree'),
        'reporting_tree_node_ids': fields.many2many('via.reporting.tree.node',
                                                    'via_report_reporting_tree_node_rel',
                                                    'via_report_id',
                                                    'tree_node_id',
                                                    string='Reporting Tree Node'),
        'analytic_acc_ids': fields.many2many('account.analytic.account',
                                             'via_report_analytic_acc_rel',
                                             'via_report_id',
                                             'analytic_acc_id',
                                             string='Analytic Accounts'),
        'acc_ids': fields.many2many('account.account',
                                    'via_report_acc_rel',
                                    'via_report_id',
                                    'acc_id',
                                    string='Accounts'),
        'acc_ids_empty_is_all': fields.boolean('Accounts When Empty Means All'),
        'journal_ids': fields.many2many('account.journal',
                                        'via_report_journal_rel',
                                        'via_report_id',
                                        'journal_id',
                                        string='Journals'),
        'journal_ids_empty_is_all': fields.boolean('Journals When Empty Means All'),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year'),
        'fiscalyear_id_2': fields.many2one('account.fiscalyear', 'Fiscal Year'),
        'target_move': fields.selection([('posted', 'All Posted Entries'),
                                         ('all', 'All Entries'),
                                         ], 'Target Moves'),
        'display_move': fields.boolean('Show Move'),
        'no_zero': fields.boolean('No Zero'),
        'use_indentation': fields.boolean('Use Indentation'),
        'no_wrap': fields.boolean('No Wrap'),
        'display_drcr': fields.boolean('Show Debit & Credit'),
        'display_large': fields.boolean('Large Format'),
        'reference_label': fields.char('Reference Label', size=128),
        'comparison_label': fields.char('Comparison Label', size=128),
        'display_comparison': fields.boolean('Enable Comparison'),
        'from_period_id': fields.many2one('account.period', 'Start Period'),
        'from_period_id_2': fields.many2one('account.period', 'Start Period'),
        'to_period_id': fields.many2one('account.period', 'End Period'),
        'to_period_id_2': fields.many2one('account.period', 'End Period'),
        'date_filter': fields.selection([('filter_no', 'No Filters'),
                                         ('filter_date', 'Date'),
                                         ('filter_period', 'Periods')], 'Filter By'),
        'date_filter_2': fields.selection([('filter_no', 'No Filters'),
                                           ('filter_date', 'Date'),
                                           ('filter_period', 'Periods')], 'Filter By'),
        'location_ids': fields.many2many('stock.location',
                                         'via_report_location_rel',
                                         'via_report_id',
                                         'location_id',
                                         string='Locations'),
        'salesman_ids': fields.many2many('res.users',
                                         'via_report_salesman_rel',
                                         'via_report_id',
                                         'salesman_id',
                                         string='Salesman'),
        'customer_ids': fields.many2many('res.partner',
                                         'via_report_customer_rel',
                                         'via_report_id',
                                         'customer_id',
                                         string='Customers'),
        'filter_selection': fields.selection(_get_filter_selection,
                                             string='Filter By'),
        'filter_selection_2': fields.selection(_get_filter_selection_2,
                                               string='Filter By'),
        'dept_ids': fields.many2many('hr.department',
                                     'via_report_dept_rel',
                                     'via_report_id',
                                     'dept_id',
                                     string='Departments'),
    }
    if float(release.major_version) < 7.0:
        _columns.update({
            'customer_addr_ids': fields.many2many('res.partner.address',
                                                  'via_report_customer_addr_rel',
                                                  'via_report_id',
                                                  'customer_addr_id',
                                                  string='Customer'),
        })

    def default_fiscalyear_id(self, cr, uid, context=None, company_id=None):
        if company_id:
            com_id = company_id
        else:
            com_id = self.pool.get('res.users').browse(cr, uid, uid,
                                                       context=context).company_id.id
        now = str(date.today())
        crit = [('company_id','=',com_id), ('date_start', '<', now), ('date_stop', '>', now)]
        fiscalyear_pool = self.pool.get('account.fiscalyear')
        fiscalyears = fiscalyear_pool.search(cr, uid, crit, limit=1)
        return fiscalyears and fiscalyears[0] or False

    _defaults = {
        'rpt_name': lambda self, cr, uid, ctx: ctx.get('via_jasper_report_utils.rpt_name', None),
        'from_mo': lambda *a: date.today().month,
        'from_yr': lambda *a: date.today().year,
        'to_mo': lambda *a: date.today().month,
        'to_yr': lambda *a: date.today().year,
        'from_dt': fields.date.context_today,
        'to_dt': fields.date.context_today,
        'from_dt_2': fields.date.context_today,
        'to_dt_2': fields.date.context_today,
        'as_of_dt': fields.date.context_today,
        'as_of_yr': lambda *a: date.today().year,
        'rpt_output': 'pdf',
        'orderby_ids': orderby_get_ids,
        'company_id': lambda self, cr, uid, ctx: self.pool.get('res.users').browse(cr, uid, uid, context=ctx).company_id.id,
        'prod_group_level': 1,
        'fiscalyear_id': default_fiscalyear_id,
        'target_move': 'posted',
        'date_filter': 'filter_no',
    }

    def default_get(self, cr, uid, fields_list, context=None):
        res = super(via_jasper_report, self).default_get(cr, uid, fields_list, context=context)

        rpt_name = context.get('via_jasper_report_utils.rpt_name', False)
        if rpt_name:
            rpt_defaults = getattr(_report_wizard_registry[normalize_rpt_name(rpt_name)], '_defaults', {})
            for field_name, field_default in rpt_defaults.iteritems():
                res[field_name] = field_default(self, cr, uid, context)

        return res

    # Related to prod_ids and prod_group_level
    def get_group_level_clause(self, cr, uid, ids, join_type='INNER', context=None):
        form = self.get_form(cr, uid, ids, context=context)
        level = form.prod_group_level
        res = (' %s JOIN product_category pc1\n'
               '  ON pc1.id = pt.categ_id\n' % join_type)
        for lvl in range(2, level + 1):
            res += (' %s JOIN product_category pc%d\n'
                    '  ON pc%d.id = pc%d.parent_id\n' % (join_type, lvl, lvl, lvl - 1))
        return res

    def get_prod_cat_ids(self, cr, uid, ids, level, prod_ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        prod_cat_pool = self.pool.get('product.category')
        sql_get_level_nodes = (' SELECT DISTINCT pp.name_template'
                               ' FROM product_product pp'
                               '  INNER JOIN product_template pt'
                               '   ON pp.product_tmpl_id = pt.id'
                               '  %s'
                               ' WHERE pp.id IN (%s)'
                               '  AND pc%d.id IS NULL')
        cr.execute(sql_get_level_nodes
                   % (form.get_group_level_clause(join_type='LEFT', context=context),
                      ','.join(str(prod_id)
                               for prod_id in prod_ids),
                      level))
        return [record[0] for record in cr.fetchall()]

    def get_prod_ids(self, cr, uid, ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        if len(form.prod_ids) == 0:
            if form.prod_ids_empty_is_none:
                return []
            crit = [('product_tmpl_id.company_id','in',[com_id.id for com_id in form.company_ids])]
            return self.pool.get('product.product').search(cr, uid,
                                                           crit,
                                                           context=context)
        else:
            return [prod_id.id for prod_id in form.prod_ids]

    def validate_prod_level(self, cr, uid, ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        if form.prod_group_level < 1:
            raise osv.except_osv(_('Error !'),
                                 _('Product Grouping Level must be at least 1 !'))

        prod_wrong_level = form.get_prod_cat_ids(form.prod_group_level,
                                                 form.get_prod_ids(context=context),
                                                 context=context)
        for prod_name in prod_wrong_level:
            raise osv.except_osv(_('Error !'),
                                 _('Product "%s" is not at Product Grouping Level !')
                                 % prod_name)
    # Related to prod_ids and prod_group_level [END]

    # Related to prod_ids_2
    def get_prod_ids_2(self, cr, uid, ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        if len(form.prod_ids_2) == 0:
            if form.prod_ids_2_empty_is_none:
                return []
            crit = [('product_tmpl_id.company_id','in',[com_id.id for com_id in form.company_ids])]
            return self.pool.get('product.product').search(cr, uid,
                                                           crit,
                                                           context=context)
        else:
            return [prod_id_2.id for prod_id_2 in form.prod_ids_2]
    # Related to prod_ids_2 [END]

    # Related to prod_lot_ids
    def get_prod_lot_ids(self, cr, uid, ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        if len(form.prod_lot_ids) == 0:
            if form.prod_lot_ids_empty_is_none:
                return []
            crit = [('product_id.company_id','in',[com_id.id for com_id in form.company_ids])]
            return self.pool.get('stock.production.lot').search(cr, uid,
                                                                crit,
                                                                context=context)
        else:
            return [prod_lot_id.id for prod_lot_id in form.prod_lot_ids]
    # Related to prod_lot_ids [END]

    # Related to prod_lot_ids_2
    def get_prod_lot_ids_2(self, cr, uid, ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        if len(form.prod_lot_ids_2) == 0:
            if form.prod_lot_ids_2_empty_is_none:
                return []
            crit = [('product_id.company_id','in',[com_id.id for com_id in form.company_ids])]
            return self.pool.get('stock.production.lot').search(cr, uid,
                                                                crit,
                                                                context=context)
        else:
            return [prod_lot_id_2.id for prod_lot_id_2 in form.prod_lot_ids_2]
    # Related to prod_lot_ids_2 [END]

    # Related to analytic_acc_ids
    def get_analytic_acc_ids(self, cr, uid, ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        if len(form.analytic_acc_ids) == 0:
            crit = [('company_id','in',[com_id.id for com_id in form.company_ids])]
            return self.pool.get('account.analytic.account').search(cr, uid,
                                                                    crit,
                                                                    context=context)
        else:
            return [analytic_acc_id.id for analytic_acc_id in form.analytic_acc_ids]

    def get_analytic_acc_names(self, cr, uid, ids, when_empty='All',
                               context=None):
        form = self.get_form(cr, uid, ids, context=context)

        return ([analytic_acc_id.name for analytic_acc_id in form.analytic_acc_ids]
                or [when_empty])
    # Related to analytic_acc_ids [END]

    # Related to reporting_tree_id and reporting_tree_node_ids
    def get_reporting_tree_node_ids(self, cr, uid, ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        if len(form.reporting_tree_node_ids) == 0:
            crit = [('tree_id','=',form.reporting_tree_id.id)]
            return self.pool.get('via.reporting.tree.node').search(cr, uid,
                                                                   crit,
                                                                   context=context)
        else:
            return [node_id.id for node_id in form.reporting_tree_node_ids]

    def get_reporting_tree_node_names(self, cr, uid, ids, when_empty='All',
                                      context=None):
        form = self.get_form(cr, uid, ids, context=context)

        return ([node_id.name for node_id in form.reporting_tree_node_ids]
                or [when_empty])
    # Related to reporting_tree_id and reporting_tree_node_ids [END]

    # Related to journal_ids
    def get_journal_ids(self, cr, uid, ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        if len(form.journal_ids) == 0:
            crit = [('company_id','in',[com_id.id for com_id in form.company_ids])]
            return self.pool.get('account.journal').search(cr, uid,
                                                           crit,
                                                           context=context)
        else:
            return [journal_id.id for journal_id in form.journal_ids]

    def get_journal_names(self, cr, uid, ids, when_empty='All', context=None):
        form = self.get_form(cr, uid, ids, context=context)

        return ([journal_id.name for journal_id in form.journal_ids]
                or [when_empty])
    # Related to journal_ids [END]

    # Related to acc_ids
    def get_acc_ids(self, cr, uid, ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        if len(form.acc_ids) == 0:
            crit = [('company_id','in',[com_id.id for com_id in form.company_ids])]
            return self.pool.get('account.account').search(cr, uid,
                                                           crit,
                                                           context=context)
        else:
            return [acc_id.id for acc_id in form.acc_ids]

    def get_acc_names(self, cr, uid, ids, when_empty='All', context=None):
        form = self.get_form(cr, uid, ids, context=context)

        return (['%s %s' % (acc_id.code, acc_id.name) for acc_id in form.acc_ids]
                or [when_empty])
    # Related to acc_ids [END]

    # Related to dept_ids
    def get_dept_ids(self, cr, uid, ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        if len(form.dept_ids) == 0:
            crit = [('company_id','in',[com_id.id for com_id in form.company_ids])]
            return self.pool.get('hr.department').search(cr, uid,
                                                         crit,
                                                         context=context)
        else:
            return [dept_id.id for dept_id in form.dept_ids]
    # Related to dept_ids [END]

    # Related to location_ids
    def get_location_ids(self, cr, uid, ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        if len(form.location_ids) == 0:
            crit = ['|',('company_id','=',False),('company_id','in',[com_id.id for com_id in form.company_ids])]
            return self.pool.get('stock.location').search(cr, uid,
                                                          crit,
                                                          context=context)
        else:
            return [location_id.id for location_id in form.location_ids]
    # Related to location_ids [END]

    # Related to salesman_ids
    def get_salesman_ids(self, cr, uid, ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)
        return [salesman_id.id for salesman_id in form.salesman_ids]
    # Related to salesman_ids [END]

    # Related to customer_ids
    def get_customer_ids(self, cr, uid, ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        if len(form.customer_ids) == 0:
            crit = [('company_id','in',[com_id.id for com_id in form.company_ids]),
                    ('customer','=',True)]
            return self.pool.get('res.partner').search(cr, uid,
                                                       crit,
                                                       context=context)
        else:
            return [customer_id.id for customer_id in form.customer_ids]
    # Related to customer_ids [END]

    if float(release.major_version) < 7.0:
        # Related to customer_addr_ids
        def get_customer_addr_ids(self, cr, uid, ids, context=None):
            form = self.get_form(cr, uid, ids, context=context)

            if len(form.customer_addr_ids) == 0:
                crit = [('company_id','in',[com_id.id for com_id in form.company_ids]),
                        ('partner_id.customer','=',True)]
                return self.pool.get('res.partner.address').search(cr, uid,
                                                                   crit,
                                                                   context=context)
            else:
                return [customer_addr_id.id for customer_addr_id in form.customer_addr_ids]
        # Related to customer_addr_ids [END]

    _date_format = '%Y-%m-%d'

    def print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}

        form = self.get_form(cr, uid, ids, context=context)
        report_wizard = _report_wizard_registry[normalize_rpt_name(form.rpt_name)](cr)
        rpt_name = report_wizard.print_report(cr, uid, form, context=context) or form.rpt_name

        # Refresh form data that might have been altered by report_wizard
        form = self.get_form(cr, uid, ids, context=context)

        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'via.jasper.report')
        data['form'] = {'id': form.id}

        (_service_name_filter,
         _service_name_filter_ctx) = report_wizard.get_service_name_filter(cr,
                                                                           uid,
                                                                           form,
                                                                           context=context)

        service_name = utility.get_service_name(cr, uid,
            rpt_name,
            form.rpt_output,
            _service_name_filter,
            _service_name_filter_ctx)

        # Redirect to reporting service
        return {'type': 'ir.actions.report.xml',
                'report_name': service_name,
                'datas': data}

    def get_form(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        return self.pool.get('via.jasper.report').browse(cr, uid, ids[0], context=context)

    def add_marshalled_data(self, cr, uid, _id, key, value):
        if isinstance(_id, list):
            _id = _id[0]
        entry = _marshalled_data_registry.setdefault(_id, {})
        entry.update({key: value})

    def _auto_init(self, cr, context=None):
        super(via_jasper_report, self)._auto_init(cr, context=context)
        # Create symbolic links to the specified generic classes to the jasper_server's custom_report directory
        _my_path = os.path.abspath(os.path.dirname(__file__))
        _my_classes = glob.glob(os.path.join(_my_path, 'report', '*.class'))

        _jr_path = addons.get_module_path('jasper_reports')
        if not _jr_path:
            raise Exception('Cannot find  "jasper_reports" module in the addon paths')

        _link_dir = os.path.join(_jr_path, 'custom_reports')
        for _class in _my_classes:
            _filename = os.path.basename(_class)
            _new_link = os.path.join(_link_dir, _filename)
            if os.path.lexists(_new_link):
                os.unlink(_new_link)
            os.symlink(_class, _new_link)

via_jasper_report()


# The following is for marshalling report parameters without going through the
# data passing activity to the OERP client that can cause a lot of troubles.
class ir_actions_report_xml(osv.osv):
    _inherit = 'ir.actions.report.xml'

    def register_all(self, cr):
        res = super(ir_actions_report_xml, self).register_all(cr)
        cr.execute("SELECT *"
                   " FROM ir_act_report_xml"
                   " WHERE report_rml ilike '%.jrxml'"
                   " ORDER BY id")
        records = cr.dictfetchall()

        class via_report_parser(object):
            def __init__(self, cr, uid, ids, data, context):
                try:
                    import release
                    import pooler
                except ImportError:
                    from openerp import release
                    from openerp import pooler

                self.cr = cr
                self.uid = uid
                self.ids = ids
                self.data = data
                self.model = self.data.get('model', False) or context.get('active_model', False)
                self.context = context or {}
                self.pool = pooler.get_pool(self.cr.dbname)
                self.parameters = {}

                # Set OERP_USER
                res_users_pool = self.pool.get('res.users')
                oerp_user = res_users_pool.browse(cr, uid, uid, context=context)
                self.parameters['OERP_USER'] = oerp_user.name

                if 'form' not in data:
                    # The user does not print through the wizard (this usually
                    # happens when the user click the print button on the RHS of
                    # the form or tree view). So, do not perform the wizard
                    # marshalling process. Performing such a process may cause
                    # a problem due to unexpected name clash over the use of
                    # OERP_ACTIVE_IDS (e.g., QCF report).
                    self.parameters['OERP_ACTIVE_IDS'] = ','.join([str(_id)
                                                                   for _id in ids])
                    return

                pool = self.pool.get('via.jasper.report')
                o = pool.browse(cr, uid, data['form']['id'], context)

                # Companies
                company_ids = ','.join(str(com_id.id)
                                       for com_id in o.company_ids)
                selected_companies = ''
                if len(company_ids) == 0:
                    company_ids = 'NULL'
                else:
                    selected_companies = ', '.join(com_id.name
                                                   for com_id in o.company_ids)

                allowed_company_ids = []

                def _get_company_ids(cr, uid, company, res):
                    res.append(company.id)
                    for com_child in company.child_ids:
                        _get_company_ids(cr, uid, com_child, res)
                _get_company_ids(cr, uid, o.company_id, allowed_company_ids)
                allowed_company_ids = ','.join(str(_id)
                                               for _id in allowed_company_ids)

                self.parameters.update({
                    'COMPANY_ID': o.company_id.id,
                    'COMPANY_NAME': o.company_id.name or '',
                    'COMPANY_CURRENCY_NAME': o.company_id.currency_id.name or '',
                    'COMPANY_IDS': company_ids,
                    'SELECTED_COMPANIES': selected_companies,
                    'ALLOWED_COMPANY_IDS': allowed_company_ids,
                })

                # State
                self.parameters.update({
                    'SELECTED_STATE': o.state or '',
                })

                # Filter selection
                self.parameters.update({
                    'SELECTED_FILTER_SELECTION': o.filter_selection or '',
                    'SELECTED_FILTER_SELECTION_2': o.filter_selection_2 or '',
                })

                # Order-by columns
                if len(o.orderby_ids):
                    self.parameters.update({
                        'ORDERBY_CLAUSE': ','.join([obj.column_name + ' ' + obj.order_dir
                                                    for obj in o.orderby_ids]),
                        'ORDERBY_CLAUSE_STR': ', '.join(obj.column_display_name + ' (' + obj.order_dir.capitalize() + ')'
                                                        for obj in o.orderby_ids),
                    })

                default_date = date.today()

                # Date type 1: granularity month
                self.parameters.update({
                    'FROM_DATE_1_YR': (o.from_yr or default_date.year),
                    'FROM_DATE_1_MO': (o.from_mo or default_date.month),
                    'FROM_DATE_1_DY': 1,
                })

                to_yr = (o.to_yr or default_date.year)
                to_mo = (o.to_mo or default_date.month)
                self.parameters.update({
                    'TO_DATE_1_YR': to_yr,
                    'TO_DATE_1_MO': to_mo,
                    'TO_DATE_1_DY': calendar.monthrange(int(to_yr),
                                                        int(to_mo))[1],
                })

                # Date type 2: granularity day
                self.parameters.update({
                    'FROM_DATE_2_YR': o.from_dt and dt(o.from_dt).year or default_date.year,
                    'FROM_DATE_2_MO': o.from_dt and dt(o.from_dt).month or default_date.month,
                    'FROM_DATE_2_DY': o.from_dt and dt(o.from_dt).day or default_date.day,
                    'TO_DATE_2_YR': o.to_dt and dt(o.to_dt).year or default_date.year,
                    'TO_DATE_2_MO': o.to_dt and dt(o.to_dt).month or default_date.month,
                    'TO_DATE_2_DY': o.to_dt and dt(o.to_dt).day or default_date.day,
                    'AS_OF_DATE_2_YR': o.as_of_dt and dt(o.as_of_dt).year or default_date.year,
                    'AS_OF_DATE_2_MO': o.as_of_dt and dt(o.as_of_dt).month or default_date.month,
                    'AS_OF_DATE_2_DY': o.as_of_dt and dt(o.as_of_dt).day or default_date.day,
                    'FROM_DATE_2_YR_2': o.from_dt_2 and dt(o.from_dt_2).year or default_date.year,
                    'FROM_DATE_2_MO_2': o.from_dt_2 and dt(o.from_dt_2).month or default_date.month,
                    'FROM_DATE_2_DY_2': o.from_dt_2 and dt(o.from_dt_2).day or default_date.day,
                    'TO_DATE_2_YR_2': o.to_dt_2 and dt(o.to_dt_2).year or default_date.year,
                    'TO_DATE_2_MO_2': o.to_dt_2 and dt(o.to_dt_2).month or default_date.month,
                    'TO_DATE_2_DY_2': o.to_dt_2 and dt(o.to_dt_2).day or default_date.day,
                })

                # Date type 3: granularity year
                self.parameters.update({
                    'AS_OF_DATE_3_YR': (o.as_of_yr or default_date.year),
                })

                # Related to prod_ids and prod_group_level
                self.parameters.update({
                    'PROD_GROUP_LEVEL': o.prod_group_level,
                    'PROD_CAT_CLAUSE': o.get_group_level_clause(join_type='LEFT', context=context),
                    'PROD_IDS': ','.join('%d' % prod_id
                                         for prod_id in o.get_prod_ids(context=context)),
                    'PROD_IDS_EMPTY_IS_NONE': o.prod_ids_empty_is_none,
                })

                # Related to prod_ids_2
                self.parameters.update({
                    'PROD_IDS_2': ','.join('%d' % prod_id_2
                                           for prod_id_2 in o.get_prod_ids_2(context=context)),
                    'PROD_IDS_2_EMPTY_IS_NONE': o.prod_ids_2_empty_is_none,
                })

                # Related to prod_lot_ids
                self.parameters.update({
                    'PROD_LOT_IDS': ','.join('%d' % prod_lot_id
                                             for prod_lot_id in o.get_prod_lot_ids(context=context)),
                    'PROD_LOT_IDS_INCLUDE_NULL': len(o.prod_lot_ids) == 0 and True or False,
                    'PROD_LOT_IDS_EMPTY_IS_NONE': o.prod_lot_ids_empty_is_none,
                })

                # Related to prod_lot_ids_2
                self.parameters.update({
                    'PROD_LOT_IDS_2': ','.join('%d' % prod_lot_id_2
                                               for prod_lot_id_2 in o.get_prod_lot_ids_2(context=context)),
                    'PROD_LOT_IDS_2_INCLUDE_NULL': len(o.prod_lot_ids_2) == 0 and True or False,
                    'PROD_LOT_IDS_2_EMPTY_IS_NONE': o.prod_lot_ids_2_empty_is_none,
                })

                # Related to reporting_tree_id and reporting_tree_node_ids
                self.parameters.update({
                    'REPORTING_TREE_ID': o.reporting_tree_id.id,
                    'REPORTING_TREE_NAME': o.reporting_tree_id.name or '',
                    'REPORTING_TREE_NODE_IDS': ','.join('%d' % node_id
                                                        for node_id in o.get_reporting_tree_node_ids(context=context)),
                    'REPORTING_TREE_NODE_NAMES': ', '.join(o.get_reporting_tree_node_names(context=context)),
                })

                # Related to analytic_acc_ids
                self.parameters.update({
                    'ANALYTIC_ACC_IDS': ','.join('%d' % analytic_acc_id
                                                 for analytic_acc_id in o.get_analytic_acc_ids(context=context)),
                    'ANALYTIC_ACC_NAMES': ', '.join(o.get_analytic_acc_names(context=context)),
                })

                # Related to acc_ids
                if o.acc_ids_empty_is_all:
                    param_acc_ids = 'NULL'
                else:
                    param_acc_ids = ','.join('%d' % acc_id
                                             for acc_id in o.get_acc_ids(context=context)),
                self.parameters.update({
                    'ACC_IDS': param_acc_ids,
                    'ACC_NAMES': ', '.join(o.get_acc_names(context=context)),
                })

                # Related to location_ids
                self.parameters.update({
                    'LOCATION_IDS': ','.join('%d' % location_id
                                        for location_id in o.get_location_ids(context=context)),
                })

                # Related to salesman_ids
                self.parameters.update({
                    'SALESMAN_IDS': ','.join('%d' % salesman_id
                                             for salesman_id in o.get_salesman_ids(context=context)),
                })

                # Related to customer_ids
                self.parameters.update({
                        'CUSTOMER_IDS': ','.join('%d' % customer_id
                                                 for customer_id in o.get_customer_ids(context=context))
                })

                if float(release.major_version) < 7.0:
                    # Related to customer_addr_ids
                    self.parameters.update({
                        'CUSTOMER_ADDR_IDS': ','.join('%d' % customer_addr_id
                                                      for customer_addr_id in o.get_customer_addr_ids(context=context))
                    })

                # Related to journal_ids
                if o.journal_ids_empty_is_all:
                    param_journal_ids = 'NULL'
                else:
                    param_journal_ids = ','.join('%d' % journal_id
                                                 for journal_id in o.get_journal_ids(context=context))
                self.parameters.update({
                    'JOURNAL_IDS': param_journal_ids,
                    'JOURNAL_NAMES': ', '.join(o.get_journal_names(context=context)),
                })

                # Related to dept_ids
                self.parameters.update({
                    'DEPT_IDS': ','.join('%d' % dept_id
                                        for dept_id in o.get_dept_ids(context=context)),
                    'DEPT_IDS_INCLUDE_NULL': len(o.dept_ids) == 0 and True or False,
                })

                fiscalyear_start_dt = (o.fiscalyear_id.period_ids
                                       and dt(o.fiscalyear_id.period_ids[0].date_start)
                                       or default_date)
                fiscalyear_stop_dt = (o.fiscalyear_id.period_ids
                                      and dt(o.fiscalyear_id.period_ids[-1].date_stop)
                                      or default_date)
                fiscalyear_start_dt_2 = (o.fiscalyear_id_2.period_ids
                                         and dt(o.fiscalyear_id_2.period_ids[0].date_start)
                                         or default_date)
                fiscalyear_stop_dt_2 = (o.fiscalyear_id_2.period_ids
                                        and dt(o.fiscalyear_id_2.period_ids[-1].date_stop)
                                        or default_date)
                self.parameters.update({
                    'FISCALYEAR_ID': o.fiscalyear_id.id,
                    'FISCALYEAR_NAME': o.fiscalyear_id.name or '',
                    'FISCALYEAR_START_YR': fiscalyear_start_dt.year,
                    'FISCALYEAR_START_MO': fiscalyear_start_dt.month,
                    'FISCALYEAR_START_DY': fiscalyear_start_dt.day,
                    'FISCALYEAR_STOP_YR': fiscalyear_stop_dt.year,
                    'FISCALYEAR_STOP_MO': fiscalyear_stop_dt.month,
                    'FISCALYEAR_STOP_DY': fiscalyear_stop_dt.day,
                    'FISCALYEAR_ID_2': o.fiscalyear_id_2.id,
                    'FISCALYEAR_NAME_2': o.fiscalyear_id_2.name or '',
                    'FISCALYEAR_START_YR_2': fiscalyear_start_dt_2.year,
                    'FISCALYEAR_START_MO_2': fiscalyear_start_dt_2.month,
                    'FISCALYEAR_START_DY_2': fiscalyear_start_dt_2.day,
                    'FISCALYEAR_STOP_YR_2': fiscalyear_stop_dt_2.year,
                    'FISCALYEAR_STOP_MO_2': fiscalyear_stop_dt_2.month,
                    'FISCALYEAR_STOP_DY_2': fiscalyear_stop_dt_2.day,
                    'TARGET_MOVE': o.target_move or '',
                    'TARGET_MOVE_NAME': (o.target_move or '').capitalize(),
                    'DISPLAY_MOVE': o.display_move,
                    'NO_ZERO': o.no_zero,
                    'USE_INDENTATION': o.use_indentation,
                    'NO_WRAP': o.no_wrap,
                    'DISPLAY_DRCR': o.display_drcr,
                    'DISPLAY_LARGE': o.display_large,
                    'REFERENCE_LABEL': o.reference_label or '',
                    'COMPARISON_LABEL': o.comparison_label or '',
                    'DISPLAY_COMPARISON': o.display_comparison,
                    'FROM_PERIOD_ID': o.from_period_id.id,
                    'FROM_PERIOD_ID_2': o.from_period_id_2.id,
                    'TO_PERIOD_ID': o.to_period_id.id,
                    'TO_PERIOD_ID_2': o.to_period_id_2.id,
                    'DATE_FILTER': o.date_filter or '',
                    'DATE_FILTER_2': o.date_filter_2 or '',
                })

                # Other marshalled data
                if o.id in _marshalled_data_registry:
                    self.parameters.update(_marshalled_data_registry[o.id])
                    del _marshalled_data_registry[o.id]

            def get(self, key, default):
                return (key == 'parameters') and self.parameters or default

        from jasper_reports.jasper_report import report_jasper

        for record in records:
            name = 'report.%s' % record['report_name']
            report_jasper(name, record['model'], via_report_parser)

        return res

ir_actions_report_xml()

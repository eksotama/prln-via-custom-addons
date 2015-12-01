# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
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

from osv import osv, fields
from tools.translate import _
import re
from via_report_webkit.ir_report import via_form_template_mako_parser, register_report


class via_form_templates(osv.osv):
    _name = 'via.form.templates'
    _description = 'Generic Template holder to be used for rendering Forms'

    def _get_output(self, cr, uid, context=None):
        _selections = [('pdf', 'PDF'), ('html', 'HTML')]
        return _selections

    def _get_engines(self, cr, uid, context=None):
        _selections = [('mako', 'Mako')]
        return _selections

    def _get_internal_name(self, cr, uid, ids, field, arg=None, context={}):
        res = {}
        for _obj in self.browse(cr, uid, ids, context=context):
            _internal_name = _obj.name
            _internal_name = re.sub(r'\s', r'_', _internal_name.strip().lower())
            res[_obj.id] = _internal_name
        return res

    _columns = {
        'name': fields.char('Name', size=64, readonly=False, required=True, select=True),
        'internal_name': fields.function(_get_internal_name, method=True, string='Internal Name', type='char', size=64),
        'model_id': fields.many2one('ir.model', 'Model', required=True, select=True, help="Model/object that the template is used to render."),
        'model': fields.related('model_id', 'model', string='Object', type='char', size=64),
        'active': fields.boolean('Active'),
        'multi': fields.boolean('Allow Multi-Document', help="Whether this form can be printed for multiple documents."),
        'tags': fields.text('Tags', select=True, help="Free text that can be used to search/filter templates to use.  Space will indicate separate tags."),
        'company_id': fields.many2one('res.company', 'Company', select=True, help="Specific company to which this template belongs to."),
        'act_report_id': fields.many2one('ir.actions.report.xml', 'Report', readonly=True, help="External ID of the Report"),
        'old_act_report_id': fields.many2one('ir.actions.report.xml', 'Report', readonly=True, help="Old External ID of the Report"),
        'webkit_header':  fields.property('ir.header_webkit', type='many2one', relation='ir.header_webkit', string='WebKit Header', help="The header linked to the report", method=True, view_load=True),
        'engine': fields.selection(_get_engines, 'Engine', select=True, required=True, help="Engine used to render the template."),
        'report_output': fields.selection(_get_output, 'Output', required=True),
        'template': fields.text('Template'),
    }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
        'active': lambda *a: False,
        'multi': lambda *a: False,
        'engine': lambda *a: 'mako',
        'report_output': lambda *a: 'pdf',
        'old_act_report_id': lambda *a: False,
    }

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Name must be unique!'),
    ]

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        _active_set = False
        for _crit in args:
            _active_set = _active_set or (_crit[0] == 'active')
            if _active_set:
                break

        if not _active_set:
            args.extend([('active', '=', True)])

        return super(via_form_templates, self).search(cr, user, args, offset=offset, limit=limit, order=order, context=context, count=count)

    def copy(self, cr, uid, id, default={}, context=None):
        _obj = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['name'] = (_obj.name or '') + '(copy)'
        return super(via_form_templates, self).copy(cr, uid, id, default=default, context=context)

    def populate_values(self, cr, uid, vals, context=None):
        _vals = vals.copy()
        return _vals

    def create(self, cr, uid, vals, context=None):
        _vals = self.populate_values(cr, uid, vals, context=context)
        vals.update(_vals)
        return super(via_form_templates, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        _vals = self.populate_values(cr, uid, vals, context=context)
        vals.update(_vals)
        return super(via_form_templates, self).write(cr, uid, ids, vals, context=context)

    def activate(self, cr, uid, ids, context=None):
        _report_obj = self.pool.get('ir.actions.report.xml')
        _xml_obj = self.pool.get('ir.model.data')
        _rpt_vals = {
            'report_type': 'webkit',
            'auto': False,
            'header': False,
            'report_file': False,
            'report_rml': False,
        }

        for _rpt in self.browse(cr, uid, ids, context=context):
            _vals = _rpt_vals.copy()
            _vals.update({
                'name': _rpt.name,
                'report_name': _rpt.internal_name,
                'model': _rpt.model,
                'multi': not _rpt.multi,
                'webkit_header': _rpt.webkit_header,
                'report_webkit_data': _rpt.template,
                'webkit_debug': bool(_rpt.report_output == 'html'),
            })

            # Check if the report has old related report, if so, update that
            if _rpt.old_act_report_id:
                _rpt.old_act_report_id.write(_vals, context=context)
                _report_id = _rpt.old_act_report_id.id
            else:
                _report_id = _report_obj.create(cr, uid, _vals, context=context) or False

            if not _report_id:
                raise osv.except_osv(_('Error'), _("Report Action creation failed for Report %s!") % (_rpt.name))

            _rpt.write({'active': True, 'act_report_id': _report_id}, context=context)

            # Register the report
            _iar = _report_obj.browse(cr, uid, _report_id, context=context)
            register_report(_iar.report_name, _iar.model, _iar.report_rml, parser=via_form_template_mako_parser, force_parser=True)
        return True

    def deactivate(self, cr, uid, ids, context=None):
        _ir_obj = self.pool.get('ir.model.data')
        for _rpt in self.browse(cr, uid, ids, context=context):
            # Update the ir_act_report_xml record so that it will not be processed by way of changing the report_type
            # Multi is set to false so that it wouldn't show in the right-side pane
            if _rpt.act_report_id:
                _rpt.act_report_id.write({'report_type': 'inactive', 'multi': False}, context=context)

            _rpt.write({'active': False, 'act_report_id': False, 'old_act_report_id': _rpt.act_report_id.id}, context=context)
        return True

via_form_templates()

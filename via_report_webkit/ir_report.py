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

from report_webkit.webkit_report import WebKitParser
from report import report_sxw

from via_l10n_id.via_tools.amount_to_text_id import amount_to_text, number_to_text, number_to_day, number_to_month, formatDate

# Imports for generate_pdf and register_report
from via_base_enhancements.tools import check_output
import tempfile
import time
import os
from tools.translate import _
from osv import osv  # , fields
import subprocess
import netsvc
import re


class via_form_template_mako_parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(via_form_template_mako_parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            # The following are set in report_sxw.rml_parse
            # 'user': browse object of the user running the form
            # 'setCompany': setCompany(company_obj) sets the company to a given company browse object
            # 'repeatIn': repeatIn(list, var_name) cycles through list and return the member one at a time in var_name
            # 'setLang': setLang(lang) sets the context's 'lang' value to the passed value (need to be a valid IETF language tag)
            # 'setTag': setTag(oldtag, newtag, attrs=None) returns the newtag and attrs as a tuple
            # 'removeParentNode': removeParentNode --> not used in webkit,
            # 'format': format(text, oldtag=None) strips leading and trailing whitespaces the passed text
            # 'formatLang': formatLang(value, digits=None, date=False, date_time=False, grouping=True, monetary=False, dp=False)
            #           formats the given object field based on the given flags
            #           - it will assume that value is numeric unless if date or date_time is set
            #           - it will use the setting configured in OpenERP based on the language set in context
            #           digits: number of digits behind decimal point, default is 2
            #           date/date_time: specifies that the given value is to be formatted as date or date_time respectively
            #           grouping: turns on digit grouping
            #           monetary: currenty have no effect
            #           dp: a Decimal Precision browse object that will be used to set digits if is not specified
            # 'lang' : user.company_id.partner_id.lang,
            # 'translate' : _translate(text) gets the translation of the given text,
            # 'setHtmlImage' : set_html_image(id, model=None, field=None, context=None)
            #           returns the value of field as specified by given database id in the given model.
            #           If model is not specified, it will return the value of field datas of ir.attachment
            # 'strip_name' : strip_name(name, maxlen=50) will returns a string of at most maxlen (default 50).
            #           If name is more than maxlen chars, it will returns maxlen-3 first character of name appended by ellipsis (...)
            # 'time' : python time object,
            # Through setCompany, the values are defaulted to user's current company:
            # 'company': browse object of the company selected
            # 'logo': company's logo attribute
            'cr': cr,  # The database connection object
            'uid': uid,  # Database ID of the user running the report
            'amount_to_text': amount_to_text,  # amount_to_text(number, lang='id', currency='Rupiah'), converts the given number to said amount
            'number_to_text': number_to_text,  # number_to_text(number), converts the given number to said number
            'number_to_day': number_to_day,  # number_to_day(number), converts the given number to the full day-of-week string representation in Bahasa Indonesia
            'number_to_month': number_to_month,  # number_to_month(number), converts the given number to the full month string representation in Bahasa Indonesia
            'formatDate': formatDate,  # formatDate(value, format='%Y-%m-%d'), formats the given date with the given format, then translate the month name to Indonesian
        })


class via_form_template_webkit_parser(WebKitParser):
    def get_lib(self, cr, uid):
        """Return the lib wkhtml path"""
        # Detect library in system first
        path = check_output('which wkhtmltopdf'.split())

        if os.path.isabs(path) and\
            os.path.exists(path) and\
            os.access(path, os.X_OK) and\
            os.path.basename(path).startswith('wkhtmltopdf'):
            _ver = check_output([path, '--version'])
            _matches = re.search(r'wkhtmltopdf ([0-9\.]+) ', _ver)
            if _matches and [int(x) for x in _matches.group(1).split(".")] > [0, 9, 9]:
                return path

        return super(via_form_template_webkit_parser, self).get_lib(cr, uid)

    def formatLang(self, value, digits=None, date=False, date_time=False, grouping=True, monetary=False):
        """Localcontext is not populated."""
        self.localcontext.update(self.parser_instance.localcontext)
        return super(via_form_template_webkit_parser, self).formatLang(value, digits=digits, date=date, date_time=date_time, grouping=grouping, monetary=monetary)

    def generate_pdf(self, comm_path, report_xml, header, footer, html_list, webkit_header=False):
        """This is an override of the original method specified in webkit_report module with some enhancements"""
        """Call webkit in order to generate pdf"""
        if not webkit_header:
            webkit_header = report_xml.webkit_header
        tmp_dir = tempfile.gettempdir()
        out = report_xml.name+str(time.time())+'.pdf'
        out = os.path.join(tmp_dir, out.replace(' ', ''))
        file_to_del = []
        if comm_path:
            command = [comm_path]
        else:
            command = ['wkhtmltopdf']

        command.append('--quiet')
        # default to UTF-8 encoding.  Use <meta charset="latin-1"> to override.
        command.extend(['--encoding', 'utf-8'])
        if header:
            head_file = file(os.path.join(tmp_dir, str(time.time()) + '.head.html'), 'w')
            head_file.write(header)
            head_file.close()
            file_to_del.append(head_file.name)
            command.extend(['--header-html', head_file.name])
        if footer:
            foot_file = file(os.path.join(tmp_dir, str(time.time()) + '.foot.html'), 'w')
            foot_file.write(footer)
            foot_file.close()
            file_to_del.append(foot_file.name)
            command.extend(['--footer-html', foot_file.name])

        if webkit_header.margin_top:
            command.extend(['--margin-top', str(webkit_header.margin_top).replace(',', '.')])
        if webkit_header.margin_bottom:
            command.extend(['--margin-bottom', str(webkit_header.margin_bottom).replace(',', '.')])
        if webkit_header.margin_left:
            command.extend(['--margin-left', str(webkit_header.margin_left).replace(',', '.')])
        if webkit_header.margin_right:
            command.extend(['--margin-right', str(webkit_header.margin_right).replace(',', '.')])
        if webkit_header.orientation:
            command.extend(['--orientation', str(webkit_header.orientation).replace(',', '.')])
        if webkit_header.format:
            if webkit_header.format == 'Custom':
                command.extend(['--page-height', str(webkit_header.paper_height).replace(',', '.')])
                command.extend(['--page-width', str(webkit_header.paper_width).replace(',', '.')])
            else:
                command.extend(['--page-size', str(webkit_header.format).replace(',', '.')])
        count = 0
        for html in html_list:
            html_file = file(os.path.join(tmp_dir, str(time.time()) + str(count) + '.body.html'), 'w')
            count += 1
            html_file.write(html)
            html_file.close()
            file_to_del.append(html_file.name)
            command.append(html_file.name)
        command.append(out)
        try:
            status = subprocess.call(command, stderr=subprocess.PIPE)  # ignore stderr
            if status:
                raise osv.except_osv(_('Webkit raise an error'), status)
        except Exception:
            for f_to_del in file_to_del:
                os.unlink(f_to_del)

        pdf = file(out, 'rb').read()
        for f_to_del in file_to_del:
            os.unlink(f_to_del)

        os.unlink(out)
        return pdf


def register_report(name, model, tmpl_path, parser=report_sxw.rml_parse, force_parser=False):
    "Register the report into the services"
    name = 'report.%s' % name
    if netsvc.Service._services.get(name, False):
        service = netsvc.Service._services[name]
        if isinstance(service, via_form_template_mako_parser):
            #already instantiated properly, skip it
            return
        if not force_parser and hasattr(service, 'parser'):
            parser = service.parser
        del netsvc.Service._services[name]
    via_form_template_webkit_parser(name, model, tmpl_path, parser=parser)


class ir_actions_report_xml(osv.osv):
    _inherit = 'ir.actions.report.xml'

    def register_all(self, cr):
        value = super(ir_actions_report_xml, self).register_all(cr)
        cr.execute("SELECT * FROM ir_act_report_xml WHERE report_type = 'webkit'")
        records = cr.dictfetchall()
        for record in records:
            register_report(record['report_name'], record['model'], record.get('report_rml', False), parser=via_form_template_mako_parser, force_parser=False)
        return value

    def create(self, cr, user, vals, context=None):
        "Create report and register it"
        res = super(ir_actions_report_xml, self).create(cr, user, vals, context=context)
        if vals.get('report_type', '') == 'webkit':
            register_report(vals['report_name'], vals['model'], vals.get('report_rml', False), parser=via_form_template_mako_parser, force_parser=False)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        "Edit report and manage it registration"
        if isinstance(ids, (int, long)):
            ids = [ids, ]

        for rep in self.browse(cr, uid, ids, context=context):
            if rep.report_type != 'webkit':
                continue

            register_report(vals.get('report_name', rep.report_name), vals.get('model', rep.model), vals.get('report_rml', rep.report_rml), parser=via_form_template_mako_parser, force_parser=False)

        res = super(ir_actions_report_xml, self).write(cr, uid, ids, vals, context=context)
        return res

ir_actions_report_xml()

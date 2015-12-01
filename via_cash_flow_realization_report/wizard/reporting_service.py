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

_jasper_report_indicator = 'jasper_report = True'
_report_table = 'ir_act_report_xml'

def get_service_name(cr, rpt_name, rpt_output, context=None):
    field = 'report_name'

    variant_clause = ''
    if rpt_output in ('xls', 'csv'):
        variant_clause += " AND report_name LIKE '%_pageless_%'"
    else:
        variant_clause += " AND report_name NOT LIKE '%_pageless_%'"

    q = (  ' SELECT ' + field
         + ' FROM ' + _report_table
         + ' WHERE ' + _jasper_report_indicator
         + " AND name = '" + rpt_name + "'"
         + " AND jasper_output = '" + rpt_output + "'"
         + variant_clause)
    cr.execute(q)

    if cr.rowcount == 1:
        return cr.fetchone()[0]
    elif cr.rowcount > 1:
        raise Exception('Report "%s" has multiple service names'
                        % (rpt_name))
    else:                
        raise Exception('Report "%s" with output "%s" has no service name'
                        % (rpt_name, rpt_output))

def get_rpt_output(self, cr, uid, context=None):
    field = 'jasper_output'

    if not isinstance(context, dict) or 'rpt_name' not in context:
        raise Exception('No report name is specified in the context')

    rpt_name = context['rpt_name']

    cr.execute('select distinct ' + field + ', upper(' + field + ')'
               + ' from ' + _report_table
               + ' where ' + _jasper_report_indicator
               + " and name = '" + rpt_name + "'"
               + ' order by ' + field)

    if cr.rowcount >= 1:
        return tuple(cr.fetchall())

    raise Exception('Report "%s" does not exist' % rpt_name)

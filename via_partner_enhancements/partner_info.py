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

from osv import osv, fields

class partner_info(osv.osv):
    _name = 'partner.info'
    _description = 'Partner Info'
    _rec_name = 'value'

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner', ondelete='cascade', required=True, select=True),
        'parameter_id': fields.many2one('partner.parameter', 'Parameter', readonly=False, required=True, help="Parameter used"),
        'value': fields.char('Value', size=512, readonly=False, required=True, select=True, help="Parameter's value"),
    }

    _sql_constraints = [
        ('partner_parameter_uniq', 'unique (partner_id,parameter_id)', 'The parameter must be unique per partner!')
    ]

partner_info()

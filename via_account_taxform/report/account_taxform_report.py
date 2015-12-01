# -*- encoding: utf-8 -*-
##############################################################################
#
#    Vikasa Infinity Anugrah, PT
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

import time
import locale
from report import report_sxw
import math


class account_taxform_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(account_taxform_report, self).__init__(cr, uid, name, context=context)

        self.localcontext.update({
            'time': time,
            'locale': locale,
            'round_currency': self.round_currency,
            'get_unit_price': self.get_unit_price,
            'get_subtotal': self.get_subtotal,
            'sum_subtotal': self.sum_subtotal,
            'sum_discount': self.sum_discount,
            'get_base': self.get_base,
            'get_ppn': self.get_ppn,
            'get_pages': self.get_pages,
        })

    def round_currency(self, currency, amount):
        rv = self.pool.get('res.currency').round(self.cr, self.uid, currency, amount )
        return rv

    def get_unit_price(self, amount, disc, qty):
        rv = (amount * 100) / (100 - (disc or 0.00)) / qty
        return rv

    def get_subtotal(self, amount, discount):
        rv = (amount * 100) / (100 - (discount or 0.00))
        return rv

    def sum_subtotal(self, taxform_lines):
        total = 0.0
        for tax in taxform_lines:
            subtotal = ((tax.price_subtotal * 100) / (100 - (tax.discount or 0.00)))
            total +=subtotal
        return total

    def sum_discount(self, taxform_lines):
        total = 0.0
        for tax in taxform_lines:
            subdiscount = (tax.discount * ((tax.price_subtotal * 100) / (100 - (tax.discount or 0.00)))) / 100
            total +=subdiscount
        return total

    def get_base(self, taxform_lines):
        total = 0.0
        total_disc = 0.0
        for tax in taxform_lines:
            subtotal = ((tax.price_subtotal * 100) / (100 - (tax.discount or 0.00)))
            total +=subtotal
            subdiscount = (tax.discount * subtotal) / 100
            total_disc +=subdiscount
        base = total - total_disc
        return base

    def get_ppn(self, taxform_lines, adv_payment):
        res = ((self.get_base(taxform_lines) - abs(adv_payment)) * 10 ) / 100
        return res

    def get_pages(self, total_lines):
        res = total_lines / 12
        return res

report_sxw.report_sxw(
    'report.account.taxform.report',
    'account.taxform',
    'addons/via_account_taxform/report/account_taxform_report.rml',
    parser=account_taxform_report
)

report_sxw.report_sxw(
    'report.account.taxform.report.one.page',
    'account.taxform',
    'addons/via_account_taxform/report/account_taxform_report_one_page.rml',
    parser=account_taxform_report
)

report_sxw.report_sxw(
    'report.account.taxform.report.preprinted',
    'account.taxform',
    'addons/via_account_taxform/report/account_taxform_report_preprinted.rml',
    parser=account_taxform_report
)

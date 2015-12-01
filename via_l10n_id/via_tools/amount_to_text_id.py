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

from tools.translate import _
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import time
import re

to_19 = [
    'Nol',
    'Satu',
    'Dua',
    'Tiga',
    'Empat',
    'Lima',
    'Enam',
    'Tujuh',
    'Delapan',
    'Sembilan',
    'Sepuluh',
    'Sebelas',
    'Dua Belas',
    'Tiga Belas',
    'Empat Belas',
    'Lima Belas',
    'Enam Belas',
    'Tujuh Belas',
    'Delapan Belas',
    'Sembilan Belas'
]
tens  = [
    'Dua Puluh',
    'Tiga Puluh',
    'Empat Puluh',
    'Lima Puluh',
    'Enam Puluh',
    'Tujuh Puluh',
    'Delapan Puluh',
    'Sembilan Puluh'
]
ribu  = [
    'Seribu',
    'Dua Ribu',
    'Tiga Ribu',
    'Empat Ribu',
    'Lima Ribu',
    'Enam Ribu',
    'Tujuh Ribu',
    'Delapan Ribu',
    'Sembilan Ribu'
]
denom = [
    '',
    'Ribu',
    'Juta',
    'Miliar',
    'Triliun',
    'Kuadriliun',
    'Kuintiliun',
    'Sextillion',
    'Septillion',
    'Octillion',
    'Nonillion',
    'Decillion',
    'Undecillion',
    'Duodecillion',
    'Tredecillion',
    'Quattuordecillion',
    'Sexdecillion',
    'Septendecillion',
    'Octodecillion',
    'Novemdecillion',
    'Vigintillion'
]
month_long = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
month_short = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agt', 'Sep', 'Okt', 'Nov', 'Des']
dow_long = ['Minggu', 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu']
month_long_en2id = {
    'January': 'Januari',
    'February': 'Februari',
    'March': 'Maret',
    'April': 'April',
    'May': 'Mei',
    'June': 'Juni',
    'July': 'Juli',
    'August': 'Agustus',
    'September': 'September',
    'October': 'Oktober',
    'November': 'November',
    'December': 'Desember',
}
month_short_en2id = {
    'Jan': 'Jan',
    'Feb': 'Feb',
    'Mar': 'Mar',
    'Apr': 'Apr',
    'May': 'Mei',
    'Jun': 'Jun',
    'Jul': 'Jul',
    'Aug': 'Agt',
    'Sep': 'Sep',
    'Oct': 'Okt',
    'Nov': 'Nov',
    'Dec': 'Des',
}


def _convert_nn(val):
    if val < 20:
        return to_19[val]
    for (dcap, dval) in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens)):
        if dval + 10 > val:
            if val % 10:
                return dcap + ' ' + to_19[val % 10]
            return dcap


def _convert_nnn(val):
    word = ''
    (mod, rem) = (val % 100, val // 100)

    if rem > 1 and rem < 10:
        word = to_19[rem] + ' Ratus'
        if mod > 0:
            word = word + ' '
    elif rem == 1:
        word = 'Seratus'
        if mod > 0:
            word = word + ' '
    if mod > 0:
        word = word + _convert_nn(mod)
    return word


def _convert_nnnn(val):
    word = ''
    (mod, rem) = (val % 1000, val // 1000)

    if rem > 1 and rem < 10:
        word = to_19[rem] + ' Ribu'
        if mod > 0:
            word = word + ' '
    elif rem == 1:
        word = 'Seribu'
        if mod > 0:
            word = word + ' '
    if mod > 0:
        word = word + _convert_nnn(mod)
    return word


def indonesian_number(val):
    if val < 100:
        return _convert_nn(val)
    if val < 1000:
        return _convert_nnn(val)
    if val < 10000:
        return _convert_nnnn(val)
    for (didx, dval) in ((v - 1, 1000 ** v) for v in range(len(denom))):
        if dval > val:
            mod = 1000 ** didx
            l = val // mod
            r = val - (l * mod)
            ret = _convert_nnn(l) + ' ' + denom[didx]
            if r > 0:
                ret = ret + ' ' + indonesian_number(r)
            return ret


def amount_to_text_id(number, currency):
    number = '%.2f' % number
    units_name = currency
    list = str(number).split('.')
    start_word = indonesian_number(int(list[0]))
    end_word = indonesian_number(int(list[1]))
    cents_number = int(list[1])
    cents_name = (cents_number > 1) and 'Sen' or 'Sen'

    final_result = start_word + ' ' + units_name
    if cents_number > 0:
        final_result += ' dan ' + end_word + ' ' + cents_name

    return final_result


def number_to_text(number):
    number = '%.2f' % number
    list = str(number).split('.')
    start_word = indonesian_number(int(list[0]))
    end_word = indonesian_number(int(list[1]))
    cents_number = int(list[1])
    cents_name = (cents_number > 1) and '' or ''

    final_result = start_word
    if cents_number > 0:
        final_result += ' koma ' + end_word

    return final_result


def number_to_day(number):
    number = int(number)
    number = min(number, len(dow_long))
    return dow_long[number]


def number_to_month(number):
    number = int(number)
    number = min(number, len(month_long))
    return month_long[number]


def number_to_mth(number):
    number = int(number)
    number = min(number, len(month_short))
    return month_short[number]


def translateToID(value, what="month_short"):
    value = value.strip()
    _dict = (what == "month_short" and month_short_en2id) or month_long_en2id
    _pattern = re.compile(r'\b(' + '|'.join(_dict.keys()) + r')\b')
    result = _pattern.sub(lambda x: _dict[x.group()], value)
    return result


def formatDate(value=False, format='%Y-%m-%d'):
    if value is False:
        # No value specified, assume NOW
        _rv = time.strftime(format)
    elif isinstance(value, float):
        # value is in seconds after epoch format
        _rv = value.strftime(format)
    elif isinstance(value, time.struct_time):
        # value is in struct_time format
        _rv = value.strftime(format)
    elif isinstance(value, (str, basestring)):
        # value is in string
        parse_format = (len(value) == len(time.strftime(DEFAULT_SERVER_DATE_FORMAT))) and \
            DEFAULT_SERVER_DATE_FORMAT or DEFAULT_SERVER_DATETIME_FORMAT
        _rv = time.strftime(format, time.strptime(value, parse_format))
    else:
        try:
            # a string-compatible format, assumed string
            # DO NOT combine this section with the first one as this check must be performed after float check
            value = str(value)
            parse_format = (len(value) == len(time.strftime(DEFAULT_SERVER_DATE_FORMAT))) and \
                DEFAULT_SERVER_DATE_FORMAT or DEFAULT_SERVER_DATETIME_FORMAT
            _rv = time.strftime(format, time.strptime(value, parse_format))
        except:
            # unrecognized format, return empty string
            _rv = ''

    # Translate the month
    if _rv:
        if bool(re.compile('%b').findall(format)):
            _rv = translateToID(_rv, what="month_short")
        elif bool(re.compile('%B').findall(format)):
            _rv = translateToID(_rv, what="month_long")

    return _rv


#-------------------------------------------------------------
# Generic functions
#-------------------------------------------------------------

_translate_funcs = {'id': amount_to_text_id}


#TODO: we should use the country AND language (ex: septante VS soixante dix)
#TODO: we should use en by default, but the translation func is yet to be implemented
def amount_to_text(nbr, lang='id', currency='Rupiah'):
    """
    Converts an integer to its textual representation, using the language set in the context if any.
    Example:
        1654: thousands six cent cinquante-quatre.
    """
    import netsvc
#    if nbr > 10000000:
#        netsvc.Logger().notifyChannel('translate', netsvc.LOG_WARNING, _("Number too large '%d', can not translate it"))
#        return str(nbr)

    if not (lang in _translate_funcs):
        netsvc.Logger().notifyChannel('translate', netsvc.LOG_WARNING, _("no translation function found for lang: '%s'" % (lang,)))
        #TODO: (default should be en) same as above
        lang = 'en'
    return _translate_funcs[lang](abs(nbr), currency)

if __name__=='__main__':
    from sys import argv

    lang = 'nl'
    if len(argv) < 2:
        for i in range(1, 200):
            print i, ">>", int_to_text(i, lang)
        for i in range(200, 999999, 139):
            print i, ">>", int_to_text(i, lang)
    else:
        print int_to_text(int(argv[1]), lang)

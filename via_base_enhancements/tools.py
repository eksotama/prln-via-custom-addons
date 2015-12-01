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


# Used for check_output
import subprocess
from subprocess import CalledProcessError

# Used for temp file utilities
from random import randint
from os import remove, SEEK_END
import hashlib


def resolve_o2m_operations(cr, uid, target_osv, operations, fields=[], context=None):
    """
    This is a copy of resolve_o2m_operations method found in account_voucher/account_voucher.py
    made available here for generic use.
    The method receive multiple form of m2o result and return a dictionary of the object read.
    The fields read can be specified.
    """
    results = []
    for operation in operations:
        result = None
        if not isinstance(operation, (list, tuple)):
            result = target_osv.read(cr, uid, operation, fields, context=context)
        elif operation[0] == 0:
            # may be necessary to check if all the fields are here and get the default values?
            result = operation[2]
        elif operation[0] == 1:
            result = target_osv.read(cr, uid, operation[1], fields, context=context)
            if not result:
                result = {}
            result.update(operation[2])
        elif operation[0] == 4:
            result = target_osv.read(cr, uid, operation[1], fields, context=context)
        if result is not None:
            results.append(result)
    return results


def prep_dict_for_write(cr, uid, val, context=None):
    """
    Prepare a dictionary for create or write method of ORM.
    The oft needed actions are translating the foreign key tuple (id, name) values
    to only the id.

    Return the passed in value unchanged in case of any error.
    """
    result = val
    if isinstance(result, dict):
        for (k, v) in result.items():
            if (isinstance(v, tuple) and (len(v) == 2)):
                result[k] = (v[0] is None and False) or v[0]
            if k in ('id', 'create_date', 'create_uid', 'write_date', 'write_uid'):
                del result[k]

    return result


def prep_dict_for_formatting(cr, uid, val, context=None):
    """
    Prepare a dictionary for string formatting operation.
    The oft needed actions are translating the foreign key tuple (id, name) values
    to only the name.

    Return the passed in value unchanged in case of any error.
    """
    result = val
    if isinstance(result, dict):
        for (k, v) in result.items():
            # Change (ID, NAME) tuples to the Name only
            if (isinstance(v, tuple) and (len(v) == 2)):
                if v[0] is None:
                    result[k] = ''
                else:
                    result[k] = v[1]
            # Change boolean value to empty string
            if (isinstance(v, bool)):
                if v is False:
                    result[k] = ''
                else:
                    result[k] = str(v)

    return result


def check_output(*popenargs, **kwargs):
    """
    This is a helper method to overcome the fact that check_output is only available
    with Python version 2.7
    """
#    if 'check_output' in dir(subprocess):
#        return subprocess.check_output(*popenargs, **kwargs)
#    else:
    _stream = ''
    _pipe = subprocess.PIPE
    try:
        if 'stdin' in kwargs:
            del kwargs['stdin']
        if 'stdout' in kwargs:
            del kwargs['stdout']
        if 'stderr' in kwargs:
            del kwargs['stderr']
        _stream = subprocess.Popen(*popenargs, stdin=_pipe, stdout=_pipe, stderr=_pipe, **kwargs).communicate()
        _stream = ' '.join(_stream)
    except:
        raise

    return _stream.strip()


def get_file_content(path=''):
    """
    This method will open a file, read all the content, and close it
    Returns the content of the file
    """
    rv = None
    try:
        _fo = open(path, 'r')
        _fo.seek(0, SEEK_END)
        _fs = _fo.tell()
        _fo.seek(-1 * _fs, SEEK_END)
        rv = _fo.read(_fs)
    except:
        raise
    finally:
        _fo.close()
    return rv


def purge_temp_file(path=''):
    """
    This method will open a temp file, write garbase into it, close it, and remove it
    """
    try:
        _fo = open(path, 'w')
        _fo.seek(0, SEEK_END)
        _fs = _fo.tell()
        _fo.seek(-1 * _fs, SEEK_END)
        _repeat = (_fs // 120) + 1
        _fo.writelines([hashlib.sha512(path).hexdigest()] * _repeat)
    finally:
        _fo.close()
        remove(path)


def write_temp_file(content=''):
    """
    This method will open a temp file, write the given content, and close it
    Returns the temp file's name
    """
    _fpath = '/tmp/%12d' % (randint(1, 999999999999))
    _fo = open(_fpath, 'w')
    _fo.write(content)
    _fo.flush()
    _fo.close()

    return _fpath

# -*- coding: utf-8 -*-
"""The larger a programming ecosystem gets, the greater the chances of
runtime variability become. Currently, Python is one of the most
widely deployed high-level programming environments available, making
it a viable target for all manner of application. But it's important
to know what you're working with.

Some basic variations that are common among development machines:

* **Executable runtime**: CPython, PyPy, Jython, etc., plus build date and compiler
* **Language version**: 2.6, 2.7, 3.3, 3.4, 3.5
* **Host operating system**: Windows, OS X, Ubuntu, Debian, CentOS, RHEL, etc.
* **Features**: 64-bit, IPv6, Unicode character support (UCS-2/UCS-4)
* **Built-in library support**: OpenSSL, threading, SQLite, zlib
* **User environment**: umask, ulimit, working directory path
* **Machine info**: CPU count, hostname, filesystem encoding

See the full example profile below for more.

ecoutils was created to quantify that variability. ecoutils quickly
produces an information-dense description of critical runtime factors,
with minimal side effects. In short, ecoutils is like browser and user
agent analytics, but for Python environments.

Transmission and collection
---------------------------

The data is all JSON serializable, and is suitable for sending to a
central analytics server. An HTTP-backed service for this can be found
at: https://github.com/mahmoud/espymetrics/

Notable omissions
-----------------

Due to space constraints (and possibly latency constraints), the
following information is deemed not dense enough, and thus omitted:

* :data:`sys.path`
* full :mod:`sysconfig`
* environment variables (:data:`os.environ`)

Compatibility
-------------

So far ecoutils has has been tested on Python 2.6, 2.7, 3.4, 3.5, and
PyPy. Various versions have been tested on Ubuntu, Debian, RHEL, OS X,
FreeBSD, and Windows 7.

Profile generation
------------------

Profiles are generated by :func:`ecoutils.get_profile`.

When run as a module, ecoutils will call :func:`~ecoutils.get_profile`
and print a profile in JSON format::

    $ python -m boltons.ecoutils
    {
      "_eco_version": "1.0.0",
      "cpu_count": 4,
      "cwd": "/home/mahmoud/projects/boltons",
      "fs_encoding": "UTF-8",
      "guid": "6b139e7bbf5ad4ed8d4063bf6235b4d2",
      "hostfqdn": "mahmoud-host",
      "hostname": "mahmoud-host",
      "linux_dist_name": "Ubuntu",
      "linux_dist_version": "14.04",
      "python": {
        "argv": "boltons/ecoutils.py",
        "bin": "/usr/bin/python",
        "build_date": "Jun 22 2015 17:58:13",
        "compiler": "GCC 4.8.2",
        "features": {
          "64bit": true,
          "expat": "expat_2.1.0",
          "ipv6": true,
          "openssl": "OpenSSL 1.0.1f 6 Jan 2014",
          "readline": true,
          "sqlite": "3.8.2",
          "threading": true,
          "tkinter": "8.6",
          "unicode_wide": true,
          "zlib": "1.2.8"
        },
        "version": "2.7.6 (default, Jun 22 2015, 17:58:13) [GCC 4.8.2]",
        "version_info": [
          2,
          7,
          6,
          "final",
          0
        ]
      },
      "time_utc": "2016-05-24 07:59:40.473140",
      "time_utc_offset": -8.0,
      "ulimit_hard": 4096,
      "ulimit_soft": 1024,
      "umask": "002",
      "uname": {
        "machine": "x86_64",
        "node": "mahmoud-host",
        "processor": "x86_64",
        "release": "3.13.0-85-generic",
        "system": "Linux",
        "version": "#129-Ubuntu SMP Thu Mar 17 20:50:15 UTC 2016"
      },
      "username": "mahmoud"
    }

``pip install boltons`` and try it yourself!
"""

# TODO: some hash of the less-dynamic bits to put it all together

import re
import os
import sys
import time
import pprint
import random
import socket
import struct
import getpass
import datetime
import platform

ECO_VERSION = '1.0.0'

PY_GT_2 = sys.version_info[0] > 2

# 128-bit GUID just like a UUID, but backwards compatible to 2.4
INSTANCE_ID = hex(random.getrandbits(128))[2:-1].lower()
IS_64BIT = struct.calcsize("P") > 4
HAVE_UCS4 = getattr(sys, 'maxunicode', 0) > 65536
HAVE_READLINE = True

try:
    import readline
except Exception:
    HAVE_READLINE = False

try:
    import sqlite3
    SQLITE_VERSION = sqlite3.sqlite_version
except Exception:
    # note: 2.5 and older have sqlite, but not sqlite3
    SQLITE_VERSION = ''


try:

    import ssl
    try:
        OPENSSL_VERSION = ssl.OPENSSL_VERSION
    except AttributeError:
        # This is a conservative estimate for Python <2.6
        # SSL module added in 2006, when 0.9.7 was standard
        OPENSSL_VERSION = 'OpenSSL >0.8.0'
except Exception:
    OPENSSL_VERSION = ''


try:
    if PY_GT_2:
        import tkinter
    else:
        import Tkinter as tkinter
    TKINTER_VERSION = str(tkinter.TkVersion)
except Exception:
    TKINTER_VERSION = ''


try:
    import zlib
    ZLIB_VERSION = zlib.ZLIB_VERSION
except Exception:
    ZLIB_VERSION = ''


try:
    from xml.parsers import expat
    EXPAT_VERSION = expat.EXPAT_VERSION
except Exception:
    EXPAT_VERSION = ''


try:
    from multiprocessing import cpu_count
    CPU_COUNT = cpu_count()
except Exception:
    CPU_COUNT = 0

try:
    import threading
    HAVE_THREADING = True
except Exception:
    HAVE_THREADING = False


try:
    HAVE_IPV6 = socket.has_ipv6
except Exception:
    HAVE_IPV6 = False


try:
    from resource import getrlimit, RLIMIT_NOFILE
    RLIMIT_FDS_SOFT, RLIMIT_FDS_HARD = getrlimit(RLIMIT_NOFILE)
except Exception:
    RLIMIT_FDS_SOFT, RLIMIT_FDS_HARD = 0, 0


START_TIME_INFO = {'time_utc': str(datetime.datetime.utcnow()),
                   'time_utc_offset': -time.timezone / 3600.0}


def get_python_info():
    ret = {}
    ret['argv'] = _escape_shell_args(sys.argv)
    ret['bin'] = sys.executable

    # Even though compiler/build_date are already here, they're
    # actually parsed from the version string. So, in the rare case of
    # the unparsable version string, we're still transmitting it.
    ret['version'] = ' '.join(sys.version.split())

    ret['compiler'] = platform.python_compiler()
    ret['build_date'] = platform.python_build()[1]
    ret['version_info'] = list(sys.version_info)

    ret['features'] = {'openssl': OPENSSL_VERSION,
                       'expat': EXPAT_VERSION,
                       'sqlite': SQLITE_VERSION,
                       'tkinter': TKINTER_VERSION,
                       'zlib': ZLIB_VERSION,
                       'unicode_wide': HAVE_UCS4,
                       'readline': HAVE_READLINE,
                       '64bit': IS_64BIT,
                       'ipv6': HAVE_IPV6,
                       'threading': HAVE_THREADING}

    return ret


def get_profile(**kwargs):
    """The main entrypoint to ecoutils. Calling this will return a
    JSON-serializable dictionary of information about the current
    process.

    It is very unlikely that the information returned will change
    during the lifetime of the process, and in most cases the majority
    of the information stays the same between runs as well.

    :func:`get_profile` takes one optional keyword argument, *scrub*,
    a :class:`bool` that, if True, blanks out identifiable
    information. This includes current working directory, hostname,
    Python executable path, command-line arguments, and
    username. Values are replaced with '-', but for compatibility keys
    remain in place.

    """
    scrub = kwargs.pop('scrub', False)
    if kwargs:
        raise TypeError('unexpected keyword arguments: %r' % (kwargs.keys(),))
    ret = {}
    try:
        ret['username'] = getpass.getuser()
    except Exception:
        ret['username'] = ''
    ret['guid'] = str(INSTANCE_ID)
    ret['hostname'] = socket.gethostname()
    ret['hostfqdn'] = socket.getfqdn()
    uname = platform.uname()
    ret['uname'] = {'system': uname[0],
                    'node': uname[1],
                    'release': uname[2],  # linux: distro name
                    'version': uname[3],  # linux: kernel version
                    'machine': uname[4],
                    'processor': uname[5]}
    try:
        linux_dist = platform.linux_distribution()
    except Exception:
        linux_dist = ('', '', '')
    ret['linux_dist_name'] = linux_dist[0]
    ret['linux_dist_version'] = linux_dist[1]
    ret['cpu_count'] = CPU_COUNT

    ret['fs_encoding'] = sys.getfilesystemencoding()
    ret['ulimit_soft'] = RLIMIT_FDS_SOFT
    ret['ulimit_hard'] = RLIMIT_FDS_HARD
    ret['cwd'] = os.getcwd()
    ret['umask'] = oct(os.umask(os.umask(2))).rjust(3, '0')

    ret['python'] = get_python_info()
    ret.update(START_TIME_INFO)
    ret['_eco_version'] = ECO_VERSION

    if scrub:
        # mask identifiable information
        ret['cwd'] = '-'
        ret['hostname'] = '-'
        ret['hostfqdn'] = '-'
        ret['python']['bin'] = '-'
        ret['python']['argv'] = '-'
        ret['uname']['node'] = '-'
        ret['username'] = '-'

    return ret


def _fake_json_dumps(val):
    # never do this. this is a hack for Python 2.4. Python 2.5 added
    # the json module for a reason.

    _real_safe_repr = pprint._safe_repr

    def _fake_safe_repr(*a, **kw):
        res, is_read, is_rec = _real_safe_repr(*a, **kw)
        if res == 'None':
            res = 'null'
        if res == 'True':
            res = 'true'
        if res == 'False':
            res = 'false'
        if not (res.startswith("'") or res.startswith("u'")):
            res = res
        else:
            if res.startswith('u'):
                res = res[1:]

            contents = res[1:-1]
            contents = contents.replace('"', '').replace(r'\"', '')
            res = '"' + contents + '"'
        return res, is_read, is_rec

    pprint._safe_repr = _fake_safe_repr
    try:
        ret = pprint.pformat(val)
    finally:
        pprint._safe_repr = _real_safe_repr

    return ret


def main():
    try:
        import json

        def dumps(val):
            return json.dumps(val, sort_keys=True, indent=2)

    except ImportError:
        dumps = _fake_json_dumps

    data_dict = get_profile()
    print(dumps(data_dict))

    return

#############################################
#  The shell escaping copied in from strutils
#############################################


def _escape_shell_args(args, sep=' ', style=None):
    if not style:
        if sys.platform == 'win32':
            style = 'cmd'
        else:
            style = 'sh'

    if style == 'sh':
        return _args2sh(args, sep=sep)
    elif style == 'cmd':
        return _args2cmd(args, sep=sep)

    raise ValueError("style expected one of 'cmd' or 'sh', not %r" % style)


_find_sh_unsafe = re.compile(r'[^a-zA-Z0-9_@%+=:,./-]').search


def _args2sh(args, sep=' '):
    # see strutils
    ret_list = []

    for arg in args:
        if not arg:
            ret_list.append("''")
            continue
        if _find_sh_unsafe(arg) is None:
            ret_list.append(arg)
            continue
        # use single quotes, and put single quotes into double quotes
        # the string $'b is then quoted as '$'"'"'b'
        ret_list.append("'" + arg.replace("'", "'\"'\"'") + "'")

    return ' '.join(ret_list)


def _args2cmd(args, sep=' '):
    # see strutils
    result = []
    needquote = False
    for arg in args:
        bs_buf = []

        # Add a space to separate this argument from the others
        if result:
            result.append(' ')

        needquote = (" " in arg) or ("\t" in arg) or not arg
        if needquote:
            result.append('"')

        for c in arg:
            if c == '\\':
                # Don't know if we need to double yet.
                bs_buf.append(c)
            elif c == '"':
                # Double backslashes.
                result.append('\\' * len(bs_buf)*2)
                bs_buf = []
                result.append('\\"')
            else:
                # Normal char
                if bs_buf:
                    result.extend(bs_buf)
                    bs_buf = []
                result.append(c)

        # Add remaining backslashes, if any.
        if bs_buf:
            result.extend(bs_buf)

        if needquote:
            result.extend(bs_buf)
            result.append('"')

    return ''.join(result)


############################
#  End shell escaping code
############################

if __name__ == '__main__':
    main()

# Written by Stephen Fromm <stephenf nero net>
# (C) 2016 University of Oregon
#
# This file is part of netspryte
#
# netspryte is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# netspryte is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with netspryte.  If not, see <http://www.gnu.org/licenses/>.

import os
import json
import logging
import logging.handlers
import tempfile
import ConfigParser
import socket

import netspryte.db
import netspryte.db.rrd

from netspryte import constants as C

def setup_logging(loglevel=C.DEFAULT_LOG_LEVEL, use_syslog=False):
    ''' set up logging '''
    C.DEFAULT_LOG_LEVEL = int(loglevel)
    if C.DEFAULT_LOG_LEVEL >= 2:
        loglevel = 'DEBUG'
    elif C.DEFAULT_LOG_LEVEL >= 1:
        loglevel = 'INFO'
    else:
        loglevel = 'WARN'

    if C.DEFAULT_VERBOSE and loglevel == 'WARN':
        loglevel = 'INFO'

    numlevel = getattr(logging, loglevel.upper(), None)
    if not isinstance(numlevel, int):
        raise ValueError('Invalid log level: %s' % loglevel)

    logargs = {}
    logargs['level'] = numlevel
    logargs['datefmt'] = '%FT%T'
    logargs['format'] = C.DEFAULT_LOG_FORMAT
    logging.basicConfig(**logargs)
    if use_syslog:
        # remove default logger and add syslog handler
        logger = logging.getLogger()
        if 'flush' in dir(logger):
            logger.flush()

        filelogger = logger.handlers[0]

        syslog = None
        try:
            syslog = logging.handlers.SysLogHandler(address='/dev/log')
            formatter = logging.Formatter('%(filename)s: %(message)s')
            syslog.setFormatter(formatter)
            logger.addHandler(syslog)
        except socket.error:
            if syslog is not None:
                syslog.close()
        else:
            logger.removeHandler(filelogger)
            if isinstance(filelogger, logging.FileHandler):
                filelogger.close()

def merge_dicts(a, b, path=None):
    if path is None:
        path = []
    for k, v in b.iteritems():
        if k in a:
            if isinstance(a[k], dict) and isinstance(v, dict):
                merge_dicts(a[k], v, path + [str(k)])
            elif a[k] == v:
                pass
            else:
                raise Exception("Conflict at %s" % k)
        else:
            a[k] = v
    return a

def json2path(data, path):
    ''' take dictionary data and write json to path '''
    try:
        dir_name = os.path.dirname(path)
        mk_path(dir_name)
        tmpfd, temp_path = tempfile.mkstemp(dir=dir_name)
        tmp = os.fdopen(tmpfd, 'w')
        json.dump(data, tmp, indent=4, sort_keys=True)
        tmp.close()
        os.rename(temp_path, path)
    except TypeError as e:
        logging.error("failed to write JSON: %s", str(e))

def data2path(data, path):
    ''' take random data and write to path '''
    try:
        dir_name = os.path.dirname(path)
        mk_path(dir_name)
        tmpfd, temp_path = tempfile.mkstemp(dir=dir_name)
        with open(temp_path, 'w') as tmp:
            tmp.write(data)
        os.close(tmpfd)
        os.rename(temp_path, path)
    except Exception as e:
        logging.error("failed to write to file: %s", str(e))

def mk_path(arg):
    if not os.path.exists(arg):
        os.makedirs(arg)

def parse_json(data):
    ''' convert json string to data structure '''
    return json.loads(data)

def parse_json_from_file(path):
    ''' read json string from path and convert to data structure '''
    try:
        data = file(path).read()
        return parse_json(data)
    except IOError:
        logging.error('file not found: %s', path)
        return None
    except Exception, e:
        logging.error('failed to parse json from file %s: %s', path, str(e))
        return None

def load_instance_data(path):
    ''' load cached data regarding collected instance
    If a site local file is found, that will also be loaded and update the returned data.
    '''
    site_data = parse_json_from_file(path)
    local_path = path.replace('.json', '-local.json')
    if os.path.exists(local_path):
        local_data = parse_json_from_file(local_path)
        site_data.update(local_data)
    return site_data

def get_db_backend():
    backends = list()
    conf_backends = C.DEFAULT_DATABASE
    for backend in conf_backends:
        if backend == "rrd":
            backends.append(netspryte.db.rrd.RrdDatabaseBackend(backend))
    if not backends:
        backends.append(netspryte.db.rrd.RrdDatabaseBackend("rrd"))
    return backends

def mk_json_filename(device, *args):
    ''' create a json filename based on the collected object '''
    parts = list()
    dev_name = device.sysName
    for arg in args:
        parts.append( arg.replace(".", "-") )
    return os.path.join(C.DEFAULT_DATADIR, dev_name, "{0}.json".format("-".join(parts)))

def mk_unique_id(device, cls, instance):
    id = list()
    for n in [ device, cls, instance ]:
        id.append(n.replace(".", "_"))
    return ".".join(id)

def clean_string(arg, replace="_"):
    for char in [' ', '.', '/', '[', ']', ':']:
        arg.replace(char, replace)
    return arg

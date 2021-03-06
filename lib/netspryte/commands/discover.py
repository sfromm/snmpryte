# Written by Stephen Fromm <stephenf nero net>
# Copyright (C) 2015-2017 University of Oregon
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

import argparse
import datetime
import os
import sys
import logging
import glob
import pprint
import traceback
import multiprocessing

import netspryte
import netspryte.snmp
from netspryte.plugins import snmp_module_loader

from netspryte.commands import BaseCommand
from netspryte import constants as C
from netspryte.utils import setup_logging, json_ready
from netspryte.utils.timer import Timer
from netspryte.manager import Manager, MeasurementInstance, MeasurementClass, Host


class DiscoverCommand(BaseCommand):

    def __init__(self, daemonize=False):
        super(DiscoverCommand, self).__init__(daemonize)
        self.parser.add_argument('devices', type=str, nargs='*',
                                 default=C.DEFAULT_DEVICES,
                                 help='list of devices to query')

    def run(self):
        args = self.parser.parse_args()
        setup_logging(args.verbose)
        t = Timer("discover")
        t.start_timer()
        cfg = C.load_config()
        num_workers = C.DEFAULT_WORKERS
        if len(args.devices) < num_workers:
            num_workers = len(args.devices)
        logging.warn("beginning discover with %s workers", num_workers)
        DiscoverCommand.SNMP_MODULES = snmp_module_loader.all()
        task_queue = multiprocessing.JoinableQueue()
        if args.nofork:
            num_workers = 1
        logging.info("creating %s workers", num_workers)
        workers = [DiscoverWorker(task_queue) for i in range(num_workers)]
        for w in workers:
            w.start()
        for d in args.devices:
            task_queue.put(d)
        # add poison pill to queue
        for i in range(num_workers):
            task_queue.put(None)
        task_queue.join()
        t.stop_timer()


class DiscoverWorker(multiprocessing.Process):

    def __init__(self, task_queue):
        multiprocessing.Process.__init__(self)
        self.task_queue = task_queue

    def run(self):
        self.mgr = Manager()
        proc_name = self.name
        t = Timer()
        while True:
            device = self.task_queue.get()
            if device is None:
                logging.info("worker %s exiting", proc_name)
                self.task_queue.task_done()
                break
            t.name = "%s discover worker" % device
            t.start_timer()
            logging.warn("processing %s", device)
            try:
                msnmp = netspryte.snmp.SNMPSession(host=device)
                for cls, module in list(DiscoverCommand.SNMP_MODULES.items()):
                    try:
                        snmp_mod = cls(msnmp)
                        name = snmp_mod.sysName or msnmp.host
                        if snmp_mod and hasattr(snmp_mod, 'data'):
                            self.process_module_data(snmp_mod)
                    except Exception as e:
                        logging.error("module %s failed against device %s: %s", cls.__name__, device, traceback.format_exc())
                        continue
            except Exception as e:
                logging.error("encountered error with %s; skipping to next device: %s", device, traceback.format_exc())
            finally:
                t.stop_timer()
            self.task_queue.task_done()
        self.mgr.close()
        return

    def process_module_data(self, snmp_mod):
        this_class_updated = False
        this_host = None
        this_class = None
        log_me = False
        these_insts = list()
        metric_types = dict()
        if not snmp_mod.data:
            return
        t = Timer("database")
        t.start_timer()
        for data in snmp_mod.data:
            now = datetime.datetime.now()
            if not this_host:
                this_host = self.mgr.get_or_create(Host, name=data['host'])
            if not this_class:
                this_class = self.mgr.get_or_create(MeasurementClass, name=data['class'], transport=data['transport'])
            if this_host is None or this_class is None:
                logging.error("encountered database error; skipping to next instance")
                continue
            t.name = "select and update database %s-%s" % (this_host.name, this_class.name)
            if not log_me:
                logging.info("updating database for %s %s", this_host.name, this_class.name)
                log_me = True
            if hasattr(snmp_mod, 'DESCRIPTION') and not this_class.description:
                this_class.description = snmp_mod.DESCRIPTION
            this_inst = self.mgr.get_or_create(MeasurementInstance,
                                          name=data['name'], index=data['index'],
                                          host=this_host, measurement_class=this_class)
            this_host.lastseen = now
            this_inst.lastseen = now
            this_inst.attrs = json_ready(data['attrs'])
            if 'presentation' in data and not this_inst.presentation:
                this_inst.presentation = json_ready(data['presentation'])
            if 'metrics' in data:
                this_inst.metrics = json_ready(data['metrics'])
                if not metric_types:
                    for k, v in list(data['metrics'].items()):
                        metric_types[k] = netspryte.snmp.get_value_type(v)
                    this_class.metric_type = json_ready(metric_types)
            self.mgr.save(this_inst)
            if this_inst.metrics:
                these_insts.append(this_inst)
        self.mgr.save(this_host)
        self.mgr.save(this_class)
        logging.info("done updating database for %s %s", this_host.name, this_class.name)
        t.stop_timer()

    # def process_device(self, device, args):
    #     try:
    #         logging.info("beginning discovery of %s", device)
    #         t = Timer("snmp discover %s" % device)
    #         t.start_timer()
    #         msnmp = netspryte.snmp.SNMPSession(host=device)
    #         data = list()
    #         snmp_modules = snmp_module_loader.all()
    #         for cls, module in snmp_modules.iteritems():
    #             mod = cls(msnmp)
    #             if mod.data:
    #                 data.extend(mod.data)
    #         t.stop_timer()
    #         pprint.pprint(data)
    #         logging.warn("%s elapsed time: %.2fs", device, t.elapsed)
    #     except Exception as e:
    #         logging.error("encountered error with %s; skipping to next device: %s", device, str(e))

# Written by Stephen Fromm <stephenf nero net>
# (C) 2016 University of Oregon
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
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

import logging
import netspryte.snmp
from netspryte.snmp.host import HostSystem

class HostEntity(HostSystem):

    DATA = {
        'entPhysicalDescr'       : '1.3.6.1.2.1.47.1.1.1.1.2',
        'entPhysicalVendorType'  : '1.3.6.1.2.1.47.1.1.1.1.3',
        'entPhysicalContainedIn' : '1.3.6.1.2.1.47.1.1.1.1.4',
        'entPhysicalClass'       : '1.3.6.1.2.1.47.1.1.1.1.5',
        'entPhysicalName'        : '1.3.6.1.2.1.47.1.1.1.1.7',
        'entPhysicalHardwareRev' : '1.3.6.1.2.1.47.1.1.1.1.8',
        'entPhysicalFirmwareRev' : '1.3.6.1.2.1.47.1.1.1.1.9',
        'entPhysicalSoftwareRev' : '1.3.6.1.2.1.47.1.1.1.1.10',
        'entPhysicalSerialNum'   : '1.3.6.1.2.1.47.1.1.1.1.11',
        'entPhysicalMfgName'     : '1.3.6.1.2.1.47.1.1.1.1.12',
        'entPhysicalModelName'   : '1.3.6.1.2.1.47.1.1.1.1.13',
        'entPhysicalAssetID'     : '1.3.6.1.2.1.47.1.1.1.1.15',
        'entPhysicalIsFRU'       : '1.3.6.1.2.1.47.1.1.1.1.16',
        'entPhysicalMfgDate'     : '1.3.6.1.2.1.47.1.1.1.1.17',
    }

    STAT = { }

    CONVERSION = {
        'entPhysicalClass': {
            1  : 'other',
            2  : 'unknown',
            3  : 'chassis',
            4  : 'backplane',
            5  : 'container',
            6  : 'powerSupply',
            7  : 'fan',
            8  : 'sensor',
            9  : 'module',
            10 : 'port',
            11 : 'stack',
            12 : 'cpu',
        },
        'entPhysicalIsFRU': {
            1 : 'true',
            2 : 'false',
        },
    }

    def __init__(self, snmp):
        self.snmp = snmp
        super(HostEntity, self).__init__(snmp)
        self._data = self._get_configuration()

    def _get_configuration(self):
        return netspryte.snmp.get_snmp_data(self.snmp, HostEntity.DATA, HostEntity.CONVERSION)

    @property
    def data(self):
        return self._data

    @property
    def entity(self):
        return self._data
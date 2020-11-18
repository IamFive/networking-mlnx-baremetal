# Copyright 2020 HuaWei Technologies. All Rights Reserved
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from neutron_lib import constants as n_const
from neutron_lib.api.definitions import portbindings

DRIVE_NAME = 'mlnx_ib_bm'
"""name of this mechanism driver"""

AUTH_STRATEGY_NONE = 'noauth'
"""Ironic API authentication strategy type"""

UFM_GROUP_NAME = 'ufm'
IRONIC_GROUP_NAME = 'ironic'
MLNX_BAREMETAL_DRIVER_GROUP_NAME = 'mlnx:baremetal'
MLNX_EXTRA_NS = 'mlnx'
"""mellanox extra properties namespace name"""

DEFAULT_IRONIC_API_VERSION = 'latest'

UNBOUND_VIF_TYPES = [portbindings.VIF_TYPE_UNBOUND,
                     portbindings.VIF_TYPE_BINDING_FAILED]

SUPPORTED_NETWORK_TYPES = [n_const.TYPE_VLAN, n_const.TYPE_VXLAN]
"""only the network which has those network types is supported by this driver. 
PKey has some function as 'vlan' for IB ports. If ethernet port has vlan set,
then we will set the PKey for IB ports in this instance.
"""

PHYSICAL_NETWORK_ANY = '*'
"""* matches any physical network include none"""

VIRTUAL_MAC_OUI_STARTS = "fe:fe:00"
"""The virtual MAC OUI starts from"""

MLNX_GUID_FIXED_SEGMENT = ['03', '00']
"""Fixed extra segment in the middle of Mellanox GUID"""

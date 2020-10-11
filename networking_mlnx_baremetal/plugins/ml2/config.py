# Copyright 2016 Mellanox Technologies, Ltd
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

from oslo_config import cfg

from networking_mlnx_baremetal import constants
from networking_mlnx_baremetal._i18n import _

DRIVER_OPTS = [
    cfg.StrOpt('endpoint',
               default='http://127.0.0.1',
               help=_('UFM REST API endpoint.')),
    cfg.StrOpt('username',
               help=_('Username for UFM REST API authentication.')),
    cfg.StrOpt('password',
               help=_('Password for UFM REST API authentication.')),
    cfg.StrOpt('verify_ca',
               default='True',
               help=_('Either a Boolean value, a path to a CA_BUNDLE '
                      'file or directory with certificates of trusted '
                      'CAs. If set to True the driver will verify the UFM'
                      'host certificates; if False the driver will '
                      'ignore verifying the SSL certificate. If it\'s '
                      'a path the driver will use the specified '
                      'certificate or one of the certificates in the '
                      'directory. Defaults to True. Optional.')),
    cfg.IntOpt('timeout',
               help=_("HTTP timeout in seconds."),
               default=10),
    cfg.ListOpt('physical_networks',
                default=constants.PHYSICAL_NETWORK_ANY,
                help=_("Comma-separated list of physical_network which this "
                       "driver should watch. * means any physical_networks "
                       "including None.")),
]


def list_opts():
    """Used to generated configuration file template for this dirver
    """
    return [(constants.MLNX_BAREMETAL_DRIVER_GROUP_NAME, DRIVER_OPTS)]


def register_opts(conf):
    """register driver options

    :param conf: oslo conf
    """
    conf.register_opts(DRIVER_OPTS,
                       group=constants.MLNX_BAREMETAL_DRIVER_GROUP_NAME)

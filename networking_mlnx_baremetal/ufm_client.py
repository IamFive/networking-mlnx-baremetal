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
import os

from ironicclient import client
from oslo_config import cfg
from oslo_utils import strutils

from networking_mlnx_baremetal._i18n import _
from networking_mlnx_baremetal import constants
from networking_mlnx_baremetal import exceptions
from networking_mlnx_baremetal.plugins.ml2 import config
from networking_mlnx_baremetal.ufmclient import client

UFM_CLIENT = None
CONF = cfg.CONF
config.register_opts(CONF)


def get_client():
    """Create an UFM REST API client instance.

    :return: an UFM REST API client instance.
    """
    global UFM_CLIENT
    if not UFM_CLIENT:
        conf = CONF[constants.MLNX_BAREMETAL_DRIVER_GROUP_NAME]
        verify_ca = conf.get('verify_ca', 'True')
        if isinstance(verify_ca, str):
            if not os.path.exists(verify_ca):
                try:
                    verify_ca = strutils.bool_from_string(verify_ca,
                                                          strict=True)
                except ValueError:
                    option = ('[%s]/verify_ca' %
                              constants.MLNX_BAREMETAL_DRIVER_GROUP_NAME)
                    details = _("The value should be a Boolean or a path "
                                "to a ca file/directory.")
                    raise exceptions.InvalidConfigValueException(
                        details=details, option=option, value=verify_ca)
        UFM_CLIENT = client.UfmClient(conf.endpoint, conf.username,
                                      conf.password, verify_ca)

    return UFM_CLIENT

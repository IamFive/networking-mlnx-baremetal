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
from networking_mlnx_baremetal.ufmclient.modules.resources import pkey
from networking_mlnx_baremetal.ufmclient.session import UfmSession


class UfmClient(object):
    """UFM API Client"""

    def __init__(self, endpoint, username, password, verify_ca):
        self._endpoint = endpoint
        self._username = username
        self._password = password
        self._verify_ca = verify_ca

        # initialize request session
        self._session = UfmSession(endpoint, username, password, verify_ca)
        # initialize UFM PKey resource client
        self._pkey = pkey.PKeyResourceClient(self._session, ufm_client=self)

    @property
    def pkey(self):
        """reference to UFM PKey resource client

        :return: UFM PKey resource client
        """
        return self._pkey

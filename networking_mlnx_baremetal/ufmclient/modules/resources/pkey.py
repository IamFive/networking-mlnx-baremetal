# -*- coding: utf-8 -*

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
from networking_mlnx_baremetal.ufmclient.modules import base
from networking_mlnx_baremetal.ufmclient import utils


class PKeyResourceClient(base.RestApiBaseClient):
    """UFM PKey resource Client"""

    def __init__(self, session, ufm_client):
        #
        """Initial a UFM PKey Resource Client

        :param session: UFM connection session
        :param ufm_client: a reference to global
            :class:`~networking_mlnx_baremetal.ufmclient.UfmClient` object
        """
        super(PKeyResourceClient, self).__init__(session, ufm_client)

    def list(self, with_guid=False):
        resp = self._session.get('/resources/pkeys?guids_data=%s' % with_guid)
        return resp.json()

    def get(self, pkey, with_guid=False):
        resp = self._session.get('/resources/pkeys/%s?guids_data=%s'
                                 % (pkey, with_guid))
        return resp.json()

    def update(self, pkey, guids, index0=False, ip_over_ib=True,
               full_membership=True):
        """Sets a list of configured GUIDs for PKey or overwrites the current
        list, if found.

        :param pkey:    indicates the identify of pkey to add. Hexadecimal
                        string between "0x0"-"0x7fff" exclusive.
        :param guids:   indicates the guid list to be added, Each GUID is a
                        hexadecimal string with a minimum length of 16
                        characters and maximum length of 20 characters.
                        examples: ["0002c903000e0b72", "0002c903000e0b73"]
        :param index0:  store the PKey at index 0 of the PKey table of the
                        GUID if true
        :param ip_over_ib: PKey is a member in a multicast group that uses IP
                           over InfiniBand
        :param full_membership: using full if true else limited
        - full: members with full membership can communicate with all hosts (
        members) within the network/partition
        - limited: members with limited membership cannot communicate with
        other members. However, communication is allowed between every other
        combination of membership types
        """
        payload = {
            "guids": [utils.mlnx_ib_client_id_to_guid(guid) for guid in guids],
            "ip_over_ib": ip_over_ib,
            "index0": index0,
            "membership": "full" if full_membership else "limited",
            "pkey": pkey
        }
        self._session.put('/resources/pkeys', payload=payload)

    def delete(self, pkey):
        self._session.delete('/resources/pkeys/%s' % pkey)

    def add_guids(self, pkey, guids, index0=True, ip_over_ib=True,
                  full_membership=True):
        """add guid list to a PKey

        :param pkey:    indicates the identify of pkey to add. Hexadecimal
                        string between "0x0"-"0x7fff" exclusive.
        :param guids:   indicates the guid list to be added, Each GUID is a
                        hexadecimal string with a minimum length of 16
                        characters and maximum length of 20 characters
        :param index0:  store the PKey at index 0 of the PKey table of the
                        GUID if true
        :param ip_over_ib: PKey is a member in a multicast group that uses IP
                           over InfiniBand
        :param full_membership: using full if true else limited
        - full: members with full membership can communicate with all hosts (
        members) within the network/partition
        - limited: members with limited membership cannot communicate with
        other members. However, communication is allowed between every other
        combination of membership types
        """
        payload = {
            "guids": [utils.mlnx_ib_client_id_to_guid(guid) for guid in guids],
            "ip_over_ib": ip_over_ib,
            "index0": index0,
            "membership": "full" if full_membership else "limited",
            "pkey": pkey
        }
        self._session.post('/resources/pkeys/', payload=payload)

    def remove_guids(self, pkey, guids):
        """remove guid list from a PKey

        DELETE /ufmRest/resources/pkeys/<pkey>/guids/<guid1>,<guid2>,...

        :param pkey:    indicates the identify of pkey to add
        :param guids:   indicates the guid list to be added
        """
        joined = ','.join([utils.mlnx_ib_client_id_to_guid(guid)
                           for guid in guids])
        self._session.delete('/resources/pkeys/%s/guids/%s' % (pkey, joined))

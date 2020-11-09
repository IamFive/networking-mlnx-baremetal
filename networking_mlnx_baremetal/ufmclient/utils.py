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
from networking_mlnx_baremetal.ufmclient import constants


def mlnx_ib_client_id_to_guid(client_id):
    """The InfiniBand address is 59 characters
    composed from GID:GUID. The last 24 characters are the
    GUID. The InfiniBand MAC is upper 10 characters and lower
    9 characters from the GUID.

    Example:
    address     - a0:00:00:27:fe:80:00:00:00:00:00:00:7c:fe:90:03:00:29:26:52
    GUID        - 7c:fe:90:03:00:29:26:52
    MAC         - 7c:fe:90:29:26:52
    client-id   - ff:00:00:00:00:00:02:00:00:02:c9:00:  + address[36:]
                  (Mellanox InfiniBand Prefix)          + address[36:]

    client-id - ff:00:00:00:00:00:02:00:00:02:c9:00:04:bd:70:03:00:37:44:86
    GUID      - 04:bd:70:03:00:37:44:86
    MAC       - 04:bd:70:37:44:86

    :param client_id: the client-id from ironic_port.extra['client-id']
    :return:
    """
    if len(client_id) == constants.IRONIC_IB_PORT_CLIENT_ID_LEN:
        return client_id[-24:].replace(':', '')

    return client_id

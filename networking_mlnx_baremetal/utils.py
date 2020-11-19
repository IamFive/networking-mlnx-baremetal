import random

from networking_mlnx_baremetal import constants
from networking_mlnx_baremetal.ufmclient import constants as ufm_const


def get_mac_from_mlnx_ib_client_id(client_id):
    """The InfiniBand address is 59 characters
    composed from GID:GUID. The last 24 characters are the
    GUID. The InfiniBand MAC is upper 10 characters and lower
    9 characters from the GUID.

    Example:
    client-id   - ff:00:00:00:00:00:02:00:00:02:c9:00:  + address[36:]
                  (Mellanox InfiniBand Prefix)          + address[36:]

    client-id - ff:00:00:00:00:00:02:00:00:02:c9:00:04:bd:70:03:00:37:44:86
                (Mellanox InfiniBand Prefix)      + address[36:]
    GUID      - 04:bd:70:03:00:37:44:86
    MAC       - 04:bd:70:37:44:86

    :param client_id: the client-id from ironic_port.extra['client-id']
    :return:
    """
    if client_id and len(client_id) == ufm_const.IRONIC_IB_PORT_CLIENT_ID_LEN:
        return client_id[-23:-15] + client_id[-9:]

    return client_id


def generate_regular_virtual_guids(client_id, count=1):
    """generate regular virtual GUID from source physical Mellanox infiniband
    port's client_id.

    GUID is composed of "MAC OUI" + "Mellanox fixed segment" + "MAC offset".

    :param client_id: the client-id from ironic_port.extra['client-id']
    :param count:     indicates the count of virtual guid to be generated
    :return:          a generator of virtual guid
    """
    assert count > 0

    source_port_mac = get_mac_from_mlnx_ib_client_id(client_id).split(':')
    mac_oui_starts = constants.VIRTUAL_MAC_OUI_STARTS.split(':')
    for offset in range(0, count):
        # generate MAC OUI
        virtual_guid = mac_oui_starts[:-1]
        mac_oui_endswith = int(mac_oui_starts[-1], 16) + offset
        virtual_guid.append(format(mac_oui_endswith, '02x'))

        # extends Mellanox fixed segment
        virtual_guid.extend(constants.MLNX_GUID_FIXED_SEGMENT)

        # add MAC address offset
        virtual_guid.extend(source_port_mac[-3:])
        yield ''.join(virtual_guid)


def generate_random_virtual_guids(count=1):
    """generate random virtual GUID.

    Random GUID will use fixed 16 bit prefix and random 32 bit suffix string.

    :param count:     indicates the count of virtual guid to be generated
    :return:          a generator of virtual guid
    """
    assert count > 0

    mac_oui_starts = constants.VIRTUAL_MAC_OUI_STARTS.split(':')
    for offset in range(0, count):
        virtual_guid = mac_oui_starts[:-1]
        virtual_guid.append(format(random.getrandbits(8), '02x'))
        virtual_guid.extend(constants.MLNX_GUID_FIXED_SEGMENT)
        virtual_guid.extend([format(random.getrandbits(8), '02x'),
                             format(random.getrandbits(8), '02x'),
                             format(random.getrandbits(8), '02x')])
        yield ''.join(virtual_guid)

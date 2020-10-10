import logging
import os
import sys

import requests

root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(root)

from oslo_config import cfg

from networking_mlnx_baremetal import ufm_client

requests.packages.urllib3.disable_warnings()
fmt = ('%(asctime)-15s [%(filename)s#%(funcName)s:%(lineno)s] '
       '%(message)s')
logging.basicConfig(format=fmt)
root_log = logging.getLogger()
root_log.setLevel(logging.DEBUG)

DEFAULT_IRONIC_API_VERSION = 'latest'
CONF = cfg.CONF

config_file_path = os.path.join(os.path.dirname(__file__), 'test.conf')
print(config_file_path)
cfg.CONF(args=["--config-file", config_file_path])

client = ufm_client.get_client()


def get_pkey(pkey_id):
    print(client.pkey.get(hex(pkey_id), with_guid=True))


## 25
# ff:00:00:00:00:00:02:00:00:02:c9:00:04:bd:70:03:00:37:47:63
# ff:00:00:00:00:00:02:00:00:02:c9:00:04:bd:70:03:00:37:47:64
guids = [
    "ff:00:00:00:00:00:02:00:00:02:c9:00:04:bd:70:03:00:37:47:63",
    "ff:00:00:00:00:00:02:00:00:02:c9:00:04:bd:70:03:00:37:47:64"
]

# guids = ['ff:00:00:00:00:00:02:00:00:02:c9:00:04:bd:70:03:00:37:44:86',
#  'ff:00:00:00:00:00:02:00:00:02:c9:00:04:bd:70:03:00:37:44:87']

# guids = [
#     "70fd450300ac38c2"
# ]

# resp = client.pkey.update(hex(10), guids, full_membership=False)
# client.pkey.delete(hex(10))

# get_pkey(10)

# client.pkey.add_guids(hex(10), guids)
# client.pkey.remove_guids(hex(10), guids)
# resp = client.pkey.add_guids(hex(3), guids)
get_pkey(10)

pkey_list = client.pkey.list(with_guid=True)
print(pkey_list)

# client.pkey.delete(hex(10))
# client.pkey.delete(hex(3))
# resp = client.pkey.delete('0x10')
# print(resp)

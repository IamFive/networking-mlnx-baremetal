import os
import sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(root)


from oslo_config import cfg

from networking_mlnx_baremetal import ironic_client

DEFAULT_IRONIC_API_VERSION = 'latest'
CONF = cfg.CONF


config_file_path = os.path.join(os.path.dirname(__file__), 'test.conf')
cfg.CONF(args=["--config-file", config_file_path])


client = ironic_client.get_client()

ports = client.port.list(detail=True)
ib_ports = [port for port in ports if port.extra.get('client-id')]
for port in ib_ports:
    print(port)
    # print("pxe enabled: %s" % port['pxe_enabled'])
    print("uuid: %s" % port.node_uuid)
    print("uuid: %s" % port.pxe_enabled)
    print("uuid: %s" % port.extra.get('client-id'))

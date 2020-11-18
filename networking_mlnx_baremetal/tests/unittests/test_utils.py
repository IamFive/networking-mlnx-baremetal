import types

from networking_mlnx_baremetal import utils
from networking_mlnx_baremetal.tests.base import TestCase


class TestUtils(TestCase):
    """ iBMC storage client unit test stubs """

    client_id = "ff:00:00:00:00:00:02:00:00:02:c9:00:04:bd:70:03:00:37:44:86"

    def testGetMacFromMlnxClientId(self):
        mac = utils.get_mac_from_mlnx_ib_client_id(self.client_id)
        self.assertEqual(mac, "04:bd:70:37:44:86")

    def testGenerateSingleVirtualGuid(self):
        guid_list = utils.generate_virtual_guids(self.client_id, count=1)
        self.assertIsInstance(guid_list, types.GeneratorType)
        self.assertEqual(list(guid_list), ["fefe000300374486"])

    def testGenerateMultipleVirtualGuid(self):
        guid_list = utils.generate_virtual_guids(self.client_id, count=5)
        self.assertIsInstance(guid_list, types.GeneratorType)
        self.assertEqual(list(guid_list), ["fefe000300374486",
                                           "fefe010300374486",
                                           "fefe020300374486",
                                           "fefe030300374486",
                                           "fefe040300374486"])

    def testZipVirtualGuid(self):
        limited_pkeys = ['0x1', '0x2']
        node_ib_client_ids = [
            'ff:00:00:00:00:00:02:00:00:02:c9:00:04:bd:70:03:00:37:44:86',
            'ff:00:00:00:00:00:02:00:00:02:c9:00:04:bd:70:03:00:37:44:87'
        ]
        virtual_guids = [
            list(utils.generate_virtual_guids(
                client_id, count=2))
            for client_id in node_ib_client_ids]

        print(zip(*virtual_guids))
        grouped = dict(zip(limited_pkeys, zip(*virtual_guids)))
        for pkey, guids in grouped.iteritems():
            print pkey
            print guids

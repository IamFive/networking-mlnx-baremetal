import string
import types

from networking_mlnx_baremetal import utils, constants
from networking_mlnx_baremetal.tests.base import TestCase


class TestUtils(TestCase):
    """ iBMC storage client unit test stubs """

    client_id = "ff:00:00:00:00:00:02:00:00:02:c9:00:04:bd:70:03:00:37:44:86"

    def testGetMacFromMlnxClientId(self):
        mac = utils.get_mac_from_mlnx_ib_client_id(self.client_id)
        self.assertEqual(mac, "04:bd:70:37:44:86")

    def testGenerateSingleVirtualGuid(self):
        guid_list = utils.generate_regular_virtual_guids(self.client_id, count=1)
        self.assertIsInstance(guid_list, types.GeneratorType)
        self.assertEqual(list(guid_list), ["fefe000300374486"])

    def testGenerateMultipleVirtualGuid(self):
        guid_list = utils.generate_regular_virtual_guids(self.client_id, count=5)
        self.assertIsInstance(guid_list, types.GeneratorType)
        self.assertEqual(list(guid_list), ["fefe000300374486",
                                           "fefe010300374486",
                                           "fefe020300374486",
                                           "fefe030300374486",
                                           "fefe040300374486"])

    def testGenerateRandomVirtualGuid(self):
        guid_list = utils.generate_random_virtual_guids(count=10000)
        self.assertIsInstance(guid_list, types.GeneratorType)

        oui = constants.VIRTUAL_MAC_OUI_STARTS.split(':')
        guids = list(guid_list)
        self.assertEqual(len(guids), 10000)
        self.assertEqual(len(set(guids)), 10000)
        for guid in list(guid_list):
            self.assertEqual(len(guid), 16)
            self.assertEqual(guid[:4], ''.join(oui[:2]))
            self.assertEqual(guid[6:10],
                             ''.join(constants.MLNX_GUID_FIXED_SEGMENT))
            self.assertEqual(all(c in string.hexdigits for c in guid), True)

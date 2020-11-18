from networking_mlnx_baremetal.tests.base import TestCase
from networking_mlnx_baremetal.ufmclient import utils


class TestUfmUtils(TestCase):
    """ iBMC storage client unit test stubs """

    client_id = "ff:00:00:00:00:00:02:00:00:02:c9:00:04:bd:70:03:00:37:44:86"

    def testMlnxClientIdToGuid(self):
        guid = utils.mlnx_ib_client_id_to_guid(self.client_id)
        self.assertEqual(guid, "04bd700300374486")

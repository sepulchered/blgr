import unittest

from blgr import BlgrCli


class TestBlgrCli(unittest.TestCase):
    def setUp(self):
        blgr = BlgrCli()

    def tearDown(self):
        blgr = None

    def test_fail(self):
        self.assertTrue(False)



if __name__ == "__main__":
    unittest.main()

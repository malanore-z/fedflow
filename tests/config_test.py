import unittest

from fedflow.config import Config


class ConfigTestCase(unittest.TestCase):

    def test_load(self):
        self.assertEqual(Config.get_property("workdir"), ".")
        Config.load("config.yaml")
        self.assertEqual(Config.get_property("workdir"), "res")
        self.assertEqual(Config.get_property("utilization-limit.cpu"), 0.9)

    def test_modify(self):
        Config.set_property("utilization-limit.cpu", 0.5)
        self.assertEqual(Config.get_property("utilization-limit.cpu"), 0.5)


if __name__ == '__main__':
    unittest.main()

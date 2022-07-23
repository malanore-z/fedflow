
import unittest

import fedflow as ff


class ScopeTest(unittest.TestCase):

    def test_base(self):
        with ff.scope("A"):
            self.assertEqual(ff.scope.scope_name, "A")
            with ff.scope("B"):
                self.assertEqual(ff.scope.scope_name, "A/B")
                with ff.scope("C"):
                    self.assertEqual(ff.scope.scope_name, "A/B/C")
                with ff.scope("D"):
                    self.assertEqual(ff.scope.scope_name, "A/B/D")
            with ff.scope("D"):
                self.assertEqual(ff.scope.scope_name, "A/D")
            self.assertEqual(ff.scope.scope_name, "A")
        self.assertEqual(ff.scope.scope_name, "")

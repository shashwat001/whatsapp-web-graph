import unittest
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

from worker import Worker

class TestWorker(unittest.TestCase):

    w = Worker()

    """
    Test if get user id parsing userid properly if user is given
    """
    def test_get_userid_for_user(self):
        userId = self.w.getUserIdIfUser('12355@abc.def.com')
        self.assertEqual(userId, '12355')

    """
    Test get exception if group is given
    """
    def test_get_userid_for_group(self):
        self.assertRaises(ValueError, self.w.getUserIdIfUser, '12355-15473@abc.def.com')

if __name__ == "__main__":
    unittest.main()
import unittest
import sys
import mock

from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

from client import WhatsApp

class TestClient(unittest.TestCase):

    """
    Test if get user id parsing userid properly if user is given
    """
    @mock.patch('worker.Worker', autospec=True)
    def test_setConnInfoParams(self, mock_worker):
        w = mock_worker.return_value
        wa = WhatsApp(w)
        wa.setConnInfoParams('asdyhiajksdfghakjsdfgh')
        print(w.secret)

if __name__ == "__main__":
    unittest.main()
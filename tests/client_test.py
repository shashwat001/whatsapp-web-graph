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
    @mock.patch('client.WhatsApp', autospec=True)
    def test_setConnInfoParams(self, mock_whatsapp):
        w = mock_whatsapp.return_value
        w.setConnInfoParams('asdyhiajksdfghakjsdfgh')
        print(w.secret.return_value)

if __name__ == "__main__":
    unittest.main()
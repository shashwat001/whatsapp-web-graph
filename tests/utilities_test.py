import unittest
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

from utilities import *

class TestWorker(unittest.TestCase):

    def test_getNextLexicographicStringAZ(self):
        self.assertEqual(getNextLexicographicString("AZ"),"BA")
    
    def test_getNextLexicographicStringA(self):
        self.assertEqual(getNextLexicographicString("A"),"B")

    def test_getNextLexicographicStringZ(self):
        self.assertEqual(getNextLexicographicString("Z"),"AA")

    def test_getNextLexicographicStringEmpty(self):
        self.assertEqual(getNextLexicographicString(""),"A")

    def test_getNextLexicographicStringNone(self):
        self.assertEqual(getNextLexicographicString(None),"A")

if __name__ == "__main__":
    unittest.main()
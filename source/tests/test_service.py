import base64
import unittest

from service import Service


class TestService(unittest.TestCase):

    def setUp(self):
        self.obj = Service()
    
    def test_one(self):
        with open("tests/data/test.png", "rb") as f:
            data = base64.b64encode(f.read())
        self.obj._img_b64_to_pil(data)

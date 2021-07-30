import base64
import unittest

from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aiohttp import web

class TestWeb(AioHTTPTestCase):

    async def get_application(self):
        self.obj = Service(model_path="../contribute/model.onnx")
        return self.obj.app
    
    @unittest_run_loop
    async def test_index(self):
        resp = await self.client.request("GET", "/")
        self.assertEqual(resp.status, 200)
    
    @unittest_run_loop
    async def test_index_success(self):
        with open("tests/data/test.png", "rb") as f:
            resp = await self.client.request("POST", "/", data={'img': f})
        self.assertEqual(resp.status, 200)
    
    @unittest_run_loop
    async def test_index_1(self):
        resp = await self.client.request("POST", "/")
        self.assertEqual(resp.status, 200)
    
    @unittest_run_loop
    async def test_index_2(self):
        resp = await self.client.request("POST", "/", data={"img": 1})
        self.assertEqual(resp.status, 200)
    
    @unittest_run_loop
    async def test_index_3(self):
        resp = await self.client.request("POST", "/", data={'img': b"h"})
        self.assertEqual(resp.status, 200)

    # @unittest_run_loop
    # async def test_json_error(self):
    #     resp = await self.client.request("POST", "/api/process", data="")
    #     self.assertEqual(resp.status, 400)
    
    # @unittest_run_loop
    # async def test_format_error(self):
    #     resp = await self.client.request("POST", "/api/process", json={})
    #     self.assertEqual(resp.status, 400)
    
    # @unittest_run_loop
    # async def test_not_image_error(self):
    #     resp = await self.client.request(
    #         "POST", "/api/process", json={"image": "hhhh"})
    #     self.assertEqual(resp.status, 400)

from service import Service


# class TestService(unittest.TestCase):

#     def setUp(self):
#         self.obj = Service(model_path="../contribute/model.onnx")
    
#     def test_one(self):
#         with open("tests/data/test.png", "rb") as f:
#             data = base64.b64encode(f.read())
#         self.obj._img_b64_to_pil(data)

#!/usr/bin/env python3

import io
import base64
from pathlib import Path

import aiohttp_cors
from aiohttp import web
from PIL import Image

from infer import CloudNetInfer


class Service:

    def __init__(self, port=8080, model_path: str = "/opt/model/model.onnx"):
        self.port = port
        self.model_path = model_path

        self.static_folder = Path("./static")

        # init
        self.app = web.Application()
        self.app.router.add_get("/health", self.h_health)
        self.app.router.add_get("/", self.h_main)
        # self.app.router.add_post("/api/process", self.h_api_process)

        self.app.router.add_static(
            "/static", self.static_folder, show_index=False)

        # CORS
        cors = aiohttp_cors.setup(
            self.app,
            defaults={
                "*": aiohttp_cors.ResourceOptions(
                    allow_credentials=False,
                    expose_headers="*",
                    allow_headers="*"
                )
            }
        )

        resource = cors.add(self.app.router.add_resource("/api/process"))
        cors.add(resource.add_route("POST", self.h_api_process))
        
        # init extern
        self.cloud = CloudNetInfer(self.model_path)
    
    def run(self):
        web.run_app(self.app)
    
    async def h_main(self, request):
        return web.Response()
    
    async def h_api_process(self, request):
        """Infer image
        
        POST request json
        format {"image": "image as base64 (png, jpg, jpeg", "agree_help": <boolean>}
        
        Answer:
        {
        "status": <string:success, error>,
        "description": "Описание ошибки",
        data: {
            {"label_idx": <int: 0>, "label_name": "название метки"}}
        }
        """
        try:
            payload = await request.json()
            img_pil = self._img_b64_to_pil(payload["image"])
            lable_idx = self.cloud.infer(img_pil)
            lable_name = self.cloud.labels[lable_idx]

            data = {
                "status": "success",
                "data": {
                    "label_idx": lable_idx,
                    "label_name": lable_name
                }
            }
        except json.decoder.JSONDecodeError as e:
            return web.json_response(self._error_data(e), status=400)
        return web.json_response(data)
    
    def _error_data(self, msg=""):
        data = {
            "status": "success",
            "description": msg
        }
        return data
    
    async def h_health(self, request):
        return web.Response(text="OK")
    
    def _img_b64_to_pil(self, img_b64: str):
        """Convert image from base64 to pil"""
        img_io = io.BytesIO(base64.b64decode(img_b64))
        img_io.seek(0)
        img_pil = Image.open(img_io)
        return img_pil


if __name__ == "__main__":
    srv = Service()
    srv.run()

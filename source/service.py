#!/usr/bin/env python3

import io
import json
import base64
import argparse
from pathlib import Path
from contextlib import asynccontextmanager

import jinja2
import aiohttp
import aiohttp_cors
import aiohttp_jinja2
from aiohttp import web
from PIL import Image, UnidentifiedImageError

from infer import CloudNetInfer


class Service:
    def __init__(self, port=8080, model_path: str = "/opt/model/model.onnx"):
        self.port = port
        self.model_path = model_path

        self.static_folder = Path("./static")

        # Init
        self.app = web.Application(client_max_size=1024 * 1024 * 20)  # Mb
        aiohttp_jinja2.setup(
            self.app, loader=jinja2.FileSystemLoader("./templates")
        )
        self.cloud = CloudNetInfer(self.model_path)

        # Routes
        self.app.router.add_get("/health", self.health)
        self.app.router.add_get("/", self.main_get)
        self.app.router.add_post("/", self.main_post)
        self.app.router.add_static(
            "/static", self.static_folder, show_index=False
        )

    def run(self):
        web.run_app(self.app)

    # -- Handlers --

    async def main_post(self, request):
        try:
            # data = await request.post()
            async with self.extract_file(request, "img") as file_field:
                img_pil = Image.open(file_field.file)
                lable_idx = self.cloud.infer(img_pil)

            answer = {
                "class_index": lable_idx,
                "class_name": self.cloud.labels[lable_idx],
            }
        except ValueError as e:
            return self.resp_main(request, is_error=True, msg=str(e))
        except UnidentifiedImageError as e:
            msg = "The file is not image"
            return self.resp_main(request, is_error=True, msg=msg)
        return self.resp_main(request, answer=answer)

    async def main_get(self, request):
        return self.resp_main(request)

    async def health(self, request):
        return web.Response(text="OK")

    # -- Other --

    def resp_main(self, request, is_error=False, msg="", answer={}):
        """
        answer: {class_index, class_name}
        """
        context = {
            "is_error": is_error,
            "error": {"msg": msg},
            "answer": answer,
        }
        response = aiohttp_jinja2.render_template(
            "index.html", request, context
        )
        return response

    @asynccontextmanager
    async def extract_file(self, request, field: str):
        """Извлекает объект файла из запроса

        Raises
            ValueError

        Return
            file_field
            filename, file_object
        """
        data = await request.post()
        img_field = data.get(field)

        if not img_field:
            raise ValueError("The {} field was not found".format(field))
        if type(img_field) != aiohttp.web_request.FileField:
            raise ValueError("The {} field is not file".format(field))

        try:
            yield img_field
        finally:
            img_field.file.close()


def arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-path", type=str, default="/opt/model/model.onnx"
    )
    parser.add_argument("--port", type=int, default=8080)
    return parser.parse_args()


if __name__ == "__main__":
    args = arguments()
    srv = Service(port=args.port, model_path=args.model_path)
    srv.run()

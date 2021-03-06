#!/usr/bin/env python3

import io
import json
import uuid
import base64
import hashlib
import argparse
from pathlib import Path
from contextlib import asynccontextmanager

import jinja2
import aiohttp
import aiohttp_cors
import aiohttp_jinja2
from aiohttp import web
from tinydb import TinyDB, Query
from PIL import Image, UnidentifiedImageError

from infer import CloudNetInfer


class Service:
    def __init__(
        self,
        port=8080,
        model_path: str = "/opt/model/model.onnx",
        store_folder: Path = None,
    ):
        self.port = port
        self.model_path = model_path
        self.store_folder = store_folder
        self.db = None

        self.static_folder = Path("./static")

        # Init
        self.app = web.Application(client_max_size=1024 * 1024 * 20)  # Mb
        aiohttp_jinja2.setup(
            self.app, loader=jinja2.FileSystemLoader("./templates")
        )
        self.cloud = CloudNetInfer(self.model_path)
        if self.store_folder is not None:
            self.db = TinyDB(store_folder.joinpath("db.json"))

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
            async with self.extract_file(request, "img") as file_field:
                img_pil = Image.open(file_field.file)
                lable_idx = self.cloud.infer(img_pil)

                if await self.check_save(request):
                    h = self.get_md5_file(file_field)
                    if not self.db.search(Query().md5 == h):
                        self.save_img(file_field, self.cloud.labels[lable_idx])
                        self.db.insert(
                            {"file_name": file_field.filename, "md5": h}
                        )

            answer = {
                "class_index": lable_idx,
                "class_name": self.cloud.labels_long[lable_idx],
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
        """?????????????????? ???????????? ?????????? ???? ??????????????

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

    def save_img(self, file_field, short_name: str):
        """?????????????????? ??????????????????????"""
        file_field.file.seek(0)

        ext = Path(file_field.filename).suffix.lower()
        filename = str(uuid.uuid4())
        p = self.store_folder.joinpath(short_name)

        if not p.is_dir():
            p.mkdir()
        p = p.joinpath("{}{}".format(filename, ext))

        with p.open("wb") as f:
            f.write(file_field.file.read())

    def get_md5_file(self, file_field):
        file_field.file.seek(0)
        h = hashlib.md5(file_field.file.read())
        return h.hexdigest()

    async def check_save(self, request) -> bool:
        """Check need save"""
        data = await request.post()
        a = data.get("check-is-aggree", False)
        b = self.db is not None
        return all([a, b])


def arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-path", type=str, default="/opt/model/model.onnx"
    )
    parser.add_argument("--store-folder", type=Path, default=None)
    parser.add_argument("--port", type=int, default=8080)
    return parser.parse_args()


if __name__ == "__main__":
    args = arguments()
    srv = Service(
        port=args.port,
        model_path=args.model_path,
        store_folder=args.store_folder,
    )
    srv.run()

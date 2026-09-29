from fastapi import FastAPI

from image_processor.api.http import create_router
from image_processor.app.use_cases.transform_image import TransformImage
from image_processor.env.tools import PillowImageTransformer


def create_app() -> FastAPI:
    app = FastAPI(title="Image processor", docs_url=None, redoc_url=None)
    app.include_router(create_router(TransformImage(PillowImageTransformer())))

    return app

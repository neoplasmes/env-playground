from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, Response
from starlette.concurrency import run_in_threadpool

from image_processor.app.ports.tools.image_transformer import InvalidImageError
from image_processor.app.use_cases.transform_image import TransformImage
from image_processor.core.entities import ImageFormat, Transformation

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def create_router(transform: TransformImage) -> APIRouter:
    router = APIRouter()

    @router.get("/healthz")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.post("/v1/transform")
    async def transform_image(
        request: Request,
        width: Annotated[int, Query(ge=1, le=4096)],
        height: Annotated[int, Query(ge=1, le=4096)],
        format: ImageFormat,
    ) -> Response:
        content = bytearray()
        async for chunk in request.stream():
            content.extend(chunk)
            if len(content) > MAX_UPLOAD_BYTES:
                raise HTTPException(status_code=413, detail="Maximum upload size is 10 MiB")
        try:
            result = await run_in_threadpool(
                transform.execute, bytes(content), Transformation(width, height, format)
            )
        except InvalidImageError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

        return Response(result.content, media_type=result.media_type)

    return router

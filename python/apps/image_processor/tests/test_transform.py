import io

import pytest
from fastapi.testclient import TestClient
from image_processor.main import create_app
from PIL import Image

client = TestClient(create_app())


def source_image() -> bytes:
    output = io.BytesIO()
    Image.new("RGBA", (80, 40), (255, 0, 0, 128)).save(output, format="PNG")

    return output.getvalue()


@pytest.mark.parametrize("format", ["png", "jpeg", "webp"])
def test_transformation_preserves_aspect_ratio(format: str) -> None:
    response = client.post(
        f"/v1/transform?width=20&height=20&format={format}", content=source_image()
    )
    assert response.status_code == 200
    with Image.open(io.BytesIO(response.content)) as result:
        assert result.size == (20, 10)
        assert result.format == format.upper()
        assert not result.getexif()


@pytest.mark.parametrize("width", [0, 4097])
def test_invalid_dimensions(width: int) -> None:
    response = client.post(
        f"/v1/transform?width={width}&height=20&format=png", content=source_image()
    )
    assert response.status_code == 422


def test_corrupt_image_is_a_client_error() -> None:
    response = client.post("/v1/transform?width=20&height=20&format=png", content=b"not an image")
    assert response.status_code == 422


def test_upload_limit() -> None:
    response = client.post(
        "/v1/transform?width=20&height=20&format=png", content=b"x" * (10 * 1024 * 1024 + 1)
    )
    assert response.status_code == 413


def test_pixel_limit() -> None:
    content = io.BytesIO()
    Image.new("RGB", (4001, 4000)).save(content, format="PNG")
    response = client.post(
        "/v1/transform?width=20&height=20&format=png", content=content.getvalue()
    )
    assert response.status_code == 422

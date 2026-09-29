from image_processor.core.entities import Transformation


def validate_transformation(transformation: Transformation) -> None:
    if not 1 <= transformation.width <= 4096 or not 1 <= transformation.height <= 4096:
        raise ValueError("Dimensions must be between 1 and 4096 pixels")
    if transformation.format not in ("png", "jpeg", "webp"):
        raise ValueError("Supported output formats: png, jpeg, webp")

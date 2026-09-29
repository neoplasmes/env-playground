from typing import Protocol

from image_processor.core.entities import ProcessedImage, Transformation


class ImageTransformer(Protocol):
    def transform(self, content: bytes, transformation: Transformation) -> ProcessedImage: ...

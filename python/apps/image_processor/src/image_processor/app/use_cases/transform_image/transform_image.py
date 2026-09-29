from image_processor.app.ports.tools.image_transformer import ImageTransformer
from image_processor.core.entities import ProcessedImage, Transformation
from image_processor.core.processes.validate_transformation import validate_transformation


class TransformImage:
    def __init__(self, transformer: ImageTransformer) -> None:
        self._transformer = transformer

    def execute(self, content: bytes, transformation: Transformation) -> ProcessedImage:
        validate_transformation(transformation)

        return self._transformer.transform(content, transformation)

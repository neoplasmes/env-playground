import io
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError

from image_processor.app.ports.tools.image_transformer import InvalidImageError
from image_processor.core.entities import ProcessedImage, Transformation


class PillowImageTransformer:
    def transform(self, content: bytes, transformation: Transformation) -> ProcessedImage:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(content)) as source:
                    if source.format not in ("PNG", "JPEG", "WEBP"):
                        raise InvalidImageError("Supported input formats: PNG, JPEG, WebP")
                    if source.width * source.height > 16_000_000:
                        raise InvalidImageError("The input image exceeds 16 megapixels")
                    if getattr(source, "is_animated", False):
                        raise InvalidImageError("Animated images are not supported")
                    source.load()
                    oriented = ImageOps.exif_transpose(source)
                    result = ImageOps.contain(
                        oriented,
                        (transformation.width, transformation.height),
                        method=Image.Resampling.LANCZOS,
                    )
                    if transformation.format == "jpeg":
                        rgba = result.convert("RGBA")
                        background = Image.new("RGB", result.size, "white")
                        background.paste(rgba, mask=rgba.getchannel("A"))
                        result = background
                    else:
                        result = result.convert("RGBA")
                    result.info.clear()
                    output = io.BytesIO()
                    result.save(output, format=transformation.format.upper())

                    return ProcessedImage(
                        content=output.getvalue(),
                        media_type=f"image/{transformation.format}",
                    )
        except InvalidImageError:
            raise
        except (
            UnidentifiedImageError,
            OSError,
            ValueError,
            Image.DecompressionBombError,
            Image.DecompressionBombWarning,
        ) as error:
            raise InvalidImageError("Invalid or unsafe image") from error

from dataclasses import dataclass
from typing import Literal

ImageFormat = Literal["png", "jpeg", "webp"]


@dataclass(frozen=True)
class Transformation:
    width: int
    height: int
    format: ImageFormat

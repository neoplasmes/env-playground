from dataclasses import dataclass


@dataclass(frozen=True)
class ProcessedImage:
    content: bytes
    media_type: str

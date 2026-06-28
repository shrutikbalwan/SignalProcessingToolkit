from __future__ import annotations

from pathlib import Path

import cv2

from src.core.constants import SUPPORTED_IMAGE_FORMATS
from src.core.exceptions import FileFormatError
from src.models.image import ImageSignal


class FileImageRepository:
    def load(self, path: Path) -> ImageSignal:
        if path.suffix.lower() not in SUPPORTED_IMAGE_FORMATS:
            raise FileFormatError(f"Unsupported image format: {path.suffix}")
        img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if img is None:
            raise FileFormatError(f"Failed to load image: {path}")
        if len(img.shape) == 2:
            color_space = "grayscale"
            h, w = img.shape
        else:
            color_space = "bgr"
            h, w = img.shape[:2]
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return ImageSignal(
            pixel_data=img,
            width=w,
            height=h,
            color_space=color_space,
            name=path.stem,
        )

    def save(self, image: ImageSignal, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        save_data = image.pixel_data
        if image.color_space == "bgr":
            save_data = cv2.cvtColor(image.pixel_data, cv2.COLOR_RGB2BGR)
        elif image.is_color:
            save_data = cv2.cvtColor(image.pixel_data, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(path), save_data)

    def get_supported_formats(self) -> set[str]:
        return SUPPORTED_IMAGE_FORMATS

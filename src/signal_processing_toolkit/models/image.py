from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ImageSignal:
    pixel_data: np.ndarray
    width: int
    height: int
    color_space: str = "grayscale"
    name: str = "Untitled Image"

    def __post_init__(self) -> None:
        if self.pixel_data.size == 0:
            raise ValueError("Image data cannot be empty")

    @property
    def shape(self) -> tuple[int, ...]:
        return self.pixel_data.shape

    @property
    def is_color(self) -> bool:
        return self.color_space != "grayscale"

    @property
    def is_grayscale(self) -> bool:
        return self.color_space == "grayscale"

    @property
    def histogram(self) -> np.ndarray:
        if self.is_grayscale:
            result: np.ndarray = np.histogram(self.pixel_data, bins=256, range=(0, 255))[0]
            return result
        histograms: list[np.ndarray] = []
        for channel in range(self.pixel_data.shape[2]):
            hist, _ = np.histogram(self.pixel_data[:, :, channel], bins=256, range=(0, 255))
            histograms.append(hist)
        return np.array(histograms)

    def to_grayscale(self) -> ImageSignal:
        if self.is_grayscale:
            return self
        gray = np.mean(self.pixel_data, axis=2).astype(np.uint8)
        return ImageSignal(pixel_data=gray, width=self.width, height=self.height, name=self.name)

    def copy(self) -> ImageSignal:
        return ImageSignal(
            pixel_data=self.pixel_data.copy(),
            width=self.width,
            height=self.height,
            color_space=self.color_space,
            name=f"{self.name} (copy)",
        )

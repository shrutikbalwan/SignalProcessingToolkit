from __future__ import annotations

from pathlib import Path

import numpy as np

from src.models.image import ImageSignal
from src.repositories.implementations.file_image_repository import FileImageRepository
from src.services.image_service import FFT2DResult, ImageService
from src.ui.viewmodels.base_viewmodel import BaseViewModel, Observable


class ImageViewModel(BaseViewModel):
    def __init__(self, image_service: ImageService) -> None:
        super().__init__()
        self._service = image_service
        self._repo = FileImageRepository()

        self.image = Observable[ImageSignal | None](None)
        self.histogram = Observable[np.ndarray | None](None)
        self.fft_result = Observable[FFT2DResult | None](None)
        self.processed_image = Observable[ImageSignal | None](None)
        self.status_message = Observable[str]("")

    def load_file(self, path: Path) -> ImageSignal | None:
        try:
            img = self._repo.load(path)
            self.image.value = img
            self.histogram.value = self._service.compute_histogram(img)
            self.fft_result.value = self._service.compute_fft2(img)
            self.status_message.value = f"Loaded: {path.name}"
            return img
        except Exception as e:
            self.status_message.value = f"Failed to load: {e}"
            return None

    def equalize(self) -> ImageSignal | None:
        img = self.image.value
        if img is None:
            return None
        result = self._service.equalize_histogram(img)
        self.processed_image.value = result
        self.status_message.value = "Histogram equalized"
        return result

    def edge_detect(self, method: str = "canny") -> ImageSignal | None:
        img = self.image.value
        if img is None:
            return None
        result = self._service.edge_detect(img, method)
        self.processed_image.value = result
        self.status_message.value = f"Edge detection: {method}"
        return result

    def fft_filter(self, cutoff: float = 0.3, filter_type: str = "lowpass") -> ImageSignal | None:
        img = self.image.value
        if img is None:
            return None
        result = self._service.fft2_filter(img, cutoff, filter_type)
        self.processed_image.value = result
        self.status_message.value = f"FFT {filter_type} filter applied"
        return result

    def blur(self, kernel_size: int = 5, method: str = "gaussian") -> ImageSignal | None:
        img = self.image.value
        if img is None:
            return None
        result = self._service.blur(img, kernel_size, method)
        self.processed_image.value = result
        self.status_message.value = f"Blur: {method}"
        return result

    def sharpen(self, strength: float = 1.0) -> ImageSignal | None:
        img = self.image.value
        if img is None:
            return None
        result = self._service.sharpen(img, strength)
        self.processed_image.value = result
        self.status_message.value = "Sharpened"
        return result

    def denoise(self, strength: int = 10) -> ImageSignal | None:
        img = self.image.value
        if img is None:
            return None
        result = self._service.denoise(img, strength)
        self.processed_image.value = result
        self.status_message.value = f"Denoised (strength={strength})"
        return result

    def morph(self, operation: str = "dilate", kernel_size: int = 3) -> ImageSignal | None:
        img = self.image.value
        if img is None:
            return None
        result = self._service.morphological(img, operation, kernel_size)
        self.processed_image.value = result
        self.status_message.value = f"Morphology: {operation}"
        return result

    def dispose(self) -> None:
        super().dispose()
        self.image.value = None
        self.processed_image.value = None

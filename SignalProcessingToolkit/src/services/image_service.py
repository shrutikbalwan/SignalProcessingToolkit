from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from src.models.image import ImageSignal
from src.models.signal import Signal


@dataclass
class FFT2DResult:
    magnitude_db: np.ndarray
    phase: np.ndarray
    magnitude_shifted: np.ndarray


class ImageService:
    def to_signal(self, image: ImageSignal, row: int | None = None) -> Signal:
        data = image.pixel_data
        if image.is_color:
            data = np.mean(data, axis=2)
        if row is not None:
            data = data[row, :]
        else:
            data = data.flatten()
        return Signal(time_data=data.astype(np.float64), sampling_rate=1000.0)

    def compute_histogram(self, image: ImageSignal) -> np.ndarray:
        return image.histogram

    def equalize_histogram(self, image: ImageSignal) -> ImageSignal:
        if image.is_grayscale:
            equalized = cv2.equalizeHist(image.pixel_data)
        else:
            ycrcb = cv2.cvtColor(image.pixel_data, cv2.COLOR_RGB2YCrCb)
            ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
            equalized = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2RGB)
        return ImageSignal(
            pixel_data=equalized,
            width=image.width,
            height=image.height,
            color_space=image.color_space,
        )

    def edge_detect(self, image: ImageSignal, method: str = "sobel") -> ImageSignal:
        gray = (
            image.pixel_data
            if image.is_grayscale
            else cv2.cvtColor(image.pixel_data, cv2.COLOR_RGB2GRAY)
        )
        if method == "sobel":
            edges = cv2.Sobel(gray, cv2.CV_64F, 1, 1)
        elif method == "canny":
            edges = cv2.Canny(gray, 100, 200)
        elif method == "laplacian":
            edges = cv2.Laplacian(gray, cv2.CV_64F)
        else:
            raise ValueError(f"Unknown edge detection method: {method}")
        return ImageSignal(
            pixel_data=np.abs(edges).astype(np.uint8),
            width=image.width,
            height=image.height,
        )

    def compute_fft2(self, image: ImageSignal) -> FFT2DResult:
        gray = (
            image.pixel_data
            if image.is_grayscale
            else cv2.cvtColor(image.pixel_data, cv2.COLOR_RGB2GRAY)
        )
        f = np.fft.fft2(gray.astype(np.float64))
        fshift = np.fft.fftshift(f)
        magnitude = np.abs(fshift)
        magnitude_db = 20 * np.log10(np.maximum(magnitude, 1e-10))
        phase = np.angle(fshift)
        return FFT2DResult(
            magnitude_db=magnitude_db,
            phase=phase,
            magnitude_shifted=magnitude,
        )

    def fft2_filter(
        self, image: ImageSignal, cutoff: float = 0.3, filter_type: str = "lowpass"
    ) -> ImageSignal:
        gray = (
            image.pixel_data
            if image.is_grayscale
            else cv2.cvtColor(image.pixel_data, cv2.COLOR_RGB2GRAY)
        )
        f = np.fft.fft2(gray.astype(np.float64))
        fshift = np.fft.fftshift(f)
        rows, cols = gray.shape
        crow, ccol = rows // 2, cols // 2
        mask: np.ndarray = np.zeros((rows, cols), np.uint8)
        r = int(min(rows, cols) * cutoff)
        if filter_type == "lowpass":
            mask = cv2.circle(mask, (ccol, crow), r, 1, -1)
        elif filter_type == "highpass":
            mask = cv2.circle(mask, (ccol, crow), r, 1, -1)
            mask = 1 - mask
        else:
            raise ValueError(f"Unknown filter type: {filter_type}")
        fshift_filtered = fshift * mask
        f_inv = np.fft.ifft2(np.fft.ifftshift(fshift_filtered))
        result = np.abs(f_inv).astype(np.uint8)
        return ImageSignal(
            pixel_data=result,
            width=image.width,
            height=image.height,
        )

    def blur(
        self, image: ImageSignal, kernel_size: int = 5, method: str = "gaussian"
    ) -> ImageSignal:
        data = image.pixel_data
        if method == "gaussian":
            blurred = cv2.GaussianBlur(data, (kernel_size, kernel_size), 0)
        elif method == "median":
            blurred = cv2.medianBlur(data, kernel_size if kernel_size % 2 == 1 else kernel_size + 1)
        elif method == "bilateral":
            blurred = cv2.bilateralFilter(data, 9, 75, 75)
        else:
            blurred = cv2.blur(data, (kernel_size, kernel_size))
        return ImageSignal(
            pixel_data=blurred,
            width=image.width,
            height=image.height,
            color_space=image.color_space,
        )

    def sharpen(self, image: ImageSignal, strength: float = 1.0) -> ImageSignal:
        kernel = np.array(
            [
                [0, -strength, 0],
                [-strength, 1 + 4 * strength, -strength],
                [0, -strength, 0],
            ]
        )
        data = image.pixel_data
        if image.is_color:
            sharpened = cv2.filter2D(data, -1, kernel)
        else:
            sharpened = cv2.filter2D(data, -1, kernel)
        sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
        return ImageSignal(
            pixel_data=sharpened,
            width=image.width,
            height=image.height,
            color_space=image.color_space,
        )

    def denoise(self, image: ImageSignal, strength: int = 10) -> ImageSignal:
        data = image.pixel_data
        denoised = cv2.fastNlMeansDenoising(data, None, strength, 7, 21)
        return ImageSignal(
            pixel_data=denoised,
            width=image.width,
            height=image.height,
            color_space=image.color_space,
        )

    def morphological(
        self, image: ImageSignal, operation: str = "dilate", kernel_size: int = 3
    ) -> ImageSignal:
        gray = (
            image.pixel_data
            if image.is_grayscale
            else cv2.cvtColor(image.pixel_data, cv2.COLOR_RGB2GRAY)
        )
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        op_map = {
            "dilate": cv2.dilate,
            "erode": cv2.erode,
            "open": cv2.morphologyEx,
            "close": cv2.morphologyEx,
            "gradient": cv2.morphologyEx,
            "tophat": cv2.morphologyEx,
            "blackhat": cv2.morphologyEx,
        }
        func = op_map.get(operation)
        if func is None:
            raise ValueError(f"Unknown morph operation: {operation}")
        result: np.ndarray
        if operation in ("open", "close", "gradient", "tophat", "blackhat"):
            morph_map = {
                "open": cv2.MORPH_OPEN,
                "close": cv2.MORPH_CLOSE,
                "gradient": cv2.MORPH_GRADIENT,
                "tophat": cv2.MORPH_TOPHAT,
                "blackhat": cv2.MORPH_BLACKHAT,
            }
            result = func(gray, morph_map[operation], kernel)  # type: ignore[operator]
        else:
            result = func(gray, kernel, iterations=1)  # type: ignore[operator]
        return ImageSignal(
            pixel_data=result,
            width=image.width,
            height=image.height,
        )

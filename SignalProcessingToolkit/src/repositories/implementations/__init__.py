import logging

from src.repositories.implementations.file_signal_repository import FileSignalRepository

try:
    from src.repositories.implementations.file_audio_repository import FileAudioRepository
except ImportError:
    logging.getLogger(__name__).warning("FileAudioRepository unavailable: install soundfile")
    FileAudioRepository = None  # type: ignore

try:
    from src.repositories.implementations.file_image_repository import FileImageRepository
except ImportError:
    logging.getLogger(__name__).warning("FileImageRepository unavailable: install opencv-python")
    FileImageRepository = None  # type: ignore

from src.repositories.implementations.file_project_repository import FileProjectRepository

__all__ = [
    "FileSignalRepository",
    "FileAudioRepository",
    "FileImageRepository",
    "FileProjectRepository",
]

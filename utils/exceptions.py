"""
Custom exceptions for AutoSubtitle Studio
"""


class SubtitleGeneratorError(Exception):
    """Base exception for subtitle generator errors"""
    pass


class AudioExtractionError(SubtitleGeneratorError):
    """Raised when audio extraction from video fails"""
    pass


class TranscriptionError(SubtitleGeneratorError):
    """Raised when transcription/subtitle generation fails"""
    pass


class SynchronizationError(SubtitleGeneratorError):
    """Raised when subtitle synchronization fails"""
    pass


class VideoValidationError(SubtitleGeneratorError):
    """Raised when video file validation fails"""
    pass


class InsufficientMemoryError(SubtitleGeneratorError):
    """Raised when insufficient memory for operation"""
    pass


class ModelLoadError(SubtitleGeneratorError):
    """Raised when AI model loading fails"""
    pass


class SubtitleFormatError(SubtitleGeneratorError):
    """Raised when subtitle format is invalid or unsupported"""
    pass


class DownloadError(SubtitleGeneratorError):
    """Raised when subtitle download fails"""
    pass

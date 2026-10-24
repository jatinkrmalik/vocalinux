"""Errors shared by microphone and system-audio capture sources."""


class CaptureStalledError(IOError):
    """The capture device stopped delivering audio frames."""

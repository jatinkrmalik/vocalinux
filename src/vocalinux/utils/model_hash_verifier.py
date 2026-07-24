"""
Model hash verification for supply chain security.

Verifies SHA256 hashes of downloaded models to detect tampering or corruption.
This is a defense-in-depth measure against supply chain attacks on model repositories.

Background:
- Hugging Face has had multiple security incidents with malicious models
- Pickle deserialization attacks can execute arbitrary code during model loading
- Hash pinning ensures we get exactly the model we expect

References:
- JFrog: ~100 malicious models found on HF (March 2024)
- ReversingLabs nullifAI: models evading Picklescan (Feb 2025)
- ShadowPickle: 63% evasion rate across all scanners (2026)
- Picklescan CVEs: CVE-2025-10155/56/57, CVSS 9.3 (Dec 2025)
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ModelHashMismatchError(Exception):
    """Raised when a downloaded model's hash doesn't match the expected value."""

    def __init__(self, filepath: str, expected: str, actual: str):
        self.filepath = filepath
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"Hash mismatch for {filepath}: "
            f"expected {expected[:16]}..., got {actual[:16]}..."
        )


def _load_hashes() -> dict:
    """Load model hashes from the JSON registry."""
    hashes_file = Path(__file__).parent / "model_hashes.json"
    try:
        with open(hashes_file, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load model hashes: {e}")
        return {}


def get_expected_hash(model_type: str, filename: str) -> Optional[str]:
    """
    Get the expected SHA256 hash for a model file.

    Args:
        model_type: One of "whispercpp", "whisper", or "vosk"
        filename: The model filename (e.g., "ggml-tiny.bin")

    Returns:
        The expected SHA256 hash, or None if not found
    """
    hashes = _load_hashes()
    model_hashes = hashes.get(model_type, {})
    return model_hashes.get(filename)


def verify_model_hash(filepath: str, expected_hash: str) -> bool:
    """
    Verify a model file's SHA256 hash against the expected value.

    Args:
        filepath: Path to the model file
        expected_hash: Expected SHA256 hash (hex string)

    Returns:
        True if hash matches

    Raises:
        ModelHashMismatchError: If hash doesn't match
    """
    sha256 = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            # Read in 8KB chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        actual_hash = sha256.hexdigest()

        if actual_hash != expected_hash:
            raise ModelHashMismatchError(filepath, expected_hash, actual_hash)

        logger.info(f"Hash verified for {Path(filepath).name}")
        return True

    except FileNotFoundError:
        logger.error(f"Model file not found: {filepath}")
        raise


def verify_download(filepath: str, model_type: str, filename: str) -> bool:
    """
    Verify a downloaded model against the hash registry.

    This is the main entry point for download verification.
    If no hash is found in the registry, logs a warning but returns True
    (graceful degradation - don't block downloads for models without hashes).

    Args:
        filepath: Path to the downloaded model file
        model_type: One of "whispercpp", "whisper", or "vosk"
        filename: The model filename

    Returns:
        True if verification passed or no hash found
        False if verification failed (file should be deleted)
    """
    expected_hash = get_expected_hash(model_type, filename)

    if expected_hash is None:
        logger.warning(
            f"No hash found for {filename} in registry. "
            f"Skipping verification. Consider adding it to model_hashes.json."
        )
        return True

    try:
        verify_model_hash(filepath, expected_hash)
        return True
    except ModelHashMismatchError as e:
        logger.error(f"Hash verification failed: {e}")
        return False

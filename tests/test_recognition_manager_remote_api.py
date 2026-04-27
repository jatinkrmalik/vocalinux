"""
Test coverage for remote API speech recognition engine.

These tests cover the remote API engine added in PR #335.
"""

import sys
import unittest
from unittest.mock import ANY, MagicMock, Mock

import pytest


# autouse fixture: inject mock modules before each test, restore sys.modules after test,
# prevent polluting other test files in the same pytest session.
@pytest.fixture(autouse=True)
def _mock_heavy_deps(monkeypatch):
    """Mock heavy dependencies via sys.modules, restoring after each test."""
    for mod in [
        "vosk",
        "whisper",
        "pyaudio",
        "wave",
        "tqdm",
        "numpy",
        "torch",
        "psutil",
    ]:
        monkeypatch.setitem(sys.modules, mod, MagicMock())

    # pywhispercpp requires submodule structure
    mock_pywhispercpp = MagicMock()
    mock_pywhispercpp.model = MagicMock()
    mock_pywhispercpp.model.Model = MagicMock()
    monkeypatch.setitem(sys.modules, "pywhispercpp", mock_pywhispercpp)
    monkeypatch.setitem(sys.modules, "pywhispercpp.model", mock_pywhispercpp.model)

    # requests needs to keep real exception classes for except statements to work properly
    mock_requests = MagicMock()
    mock_requests.exceptions.ConnectionError = ConnectionError
    mock_requests.exceptions.RequestException = Exception
    monkeypatch.setitem(sys.modules, "requests", mock_requests)

    yield


def _import_manager():
    """Delayed import of SpeechRecognitionManager to ensure fixture mocks take effect before execution."""
    from vocalinux.speech_recognition.recognition_manager import (
        SpeechRecognitionManager,
    )

    return SpeechRecognitionManager


def _get_mock_requests():
    """Get the mock requests object currently injected into sys.modules."""
    return sys.modules["requests"]


def _setup_requests_get_ok(status_code=200):
    """Configure mock requests.get to return a successful response."""
    mock_requests = _get_mock_requests()
    mock_response = Mock()
    mock_response.ok = True
    mock_response.status_code = status_code
    mock_requests.get.return_value = mock_response
    return mock_requests.get


def _setup_requests_get_error(exception):
    """Configure mock requests.get to throw an exception."""
    mock_requests = _get_mock_requests()
    mock_requests.get.side_effect = exception
    return mock_requests.get


def _setup_requests_get_non_ok(status_code=500):
    """Configure mock requests.get to return a non-successful response."""
    mock_requests = _get_mock_requests()
    mock_response = Mock()
    mock_response.ok = False
    mock_response.status_code = status_code
    mock_requests.get.return_value = mock_response
    return mock_requests.get


def _setup_requests_post_ok(json_data, status_code=200):
    """Configure mock requests.post to return a successful response."""
    mock_requests = _get_mock_requests()
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data
    mock_requests.post.return_value = mock_response
    return mock_requests.post


def _setup_requests_post_error(exception):
    """Configure mock requests.post to throw an exception."""
    mock_requests = _get_mock_requests()
    mock_requests.post.side_effect = exception
    return mock_requests.post


def _setup_requests_post_status(status_code, raise_for_status_error=None):
    """Configure mock requests.post to return a response with a specific status code."""
    mock_requests = _get_mock_requests()
    mock_response = Mock()
    mock_response.status_code = status_code
    if raise_for_status_error:
        mock_response.raise_for_status.side_effect = raise_for_status_error
    mock_requests.post.return_value = mock_response
    return mock_requests.post


class TestRemoteAPIEngine(unittest.TestCase):
    """Test cases for remote API speech recognition engine."""

    def test_remote_api_init_without_url(self):
        """Test remote API initialization without URL."""
        SpeechRecognitionManager = _import_manager()
        manager = SpeechRecognitionManager(
            engine="remote_api",
            remote_api_url="",
        )
        # Should not raise, just set _model_initialized to False
        self.assertFalse(manager._model_initialized)

    def test_remote_api_init_with_invalid_url(self):
        """Test remote API initialization with invalid URL format."""
        SpeechRecognitionManager = _import_manager()
        manager = SpeechRecognitionManager(
            engine="remote_api",
            remote_api_url="invalid-url",
        )
        # Should not raise, just set _model_initialized to False
        self.assertFalse(manager._model_initialized)

    def test_remote_api_init_with_valid_url(self):
        """Test remote API initialization with valid HTTP URL."""
        SpeechRecognitionManager = _import_manager()
        _setup_requests_get_ok()

        manager = SpeechRecognitionManager(
            engine="remote_api",
            remote_api_url="http://localhost:9090",
        )
        # Should set _model_initialized to True
        self.assertTrue(manager._model_initialized)

    def test_remote_api_init_with_valid_https_url(self):
        """Test remote API initialization with HTTPS URL."""
        SpeechRecognitionManager = _import_manager()
        _setup_requests_get_ok()

        manager = SpeechRecognitionManager(
            engine="remote_api",
            remote_api_url="https://192.168.1.100:9090",
        )
        self.assertTrue(manager._model_initialized)

    def test_remote_api_init_strips_trailing_slash(self):
        """Test remote API initialization strips trailing slash from URL."""
        SpeechRecognitionManager = _import_manager()
        _setup_requests_get_ok()

        manager = SpeechRecognitionManager(
            engine="remote_api",
            remote_api_url="http://localhost:9090/",
        )
        # URL should have trailing slash stripped
        self.assertFalse(manager.remote_api_url.endswith("/"))

    def test_remote_api_init_with_connection_failure(self):
        """Test remote API initialization handles connection failure gracefully."""
        SpeechRecognitionManager = _import_manager()
        _setup_requests_get_error(Exception("Connection refused"))

        manager = SpeechRecognitionManager(
            engine="remote_api",
            remote_api_url="http://localhost:9090",
        )
        # Should still set _model_initialized to True (will retry later)
        self.assertTrue(manager._model_initialized)

    def test_remote_api_init_with_server_error(self):
        """Test remote API initialization handles non-OK server response."""
        SpeechRecognitionManager = _import_manager()
        _setup_requests_get_non_ok(status_code=500)

        manager = SpeechRecognitionManager(
            engine="remote_api",
            remote_api_url="http://localhost:9090",
        )
        # Should still set _model_initialized to True (warns but continues)
        self.assertTrue(manager._model_initialized)

    def test_remote_api_init_with_api_key(self):
        """Test remote API initialization includes API key in headers."""
        SpeechRecognitionManager = _import_manager()
        mock_get = _setup_requests_get_ok()

        manager = SpeechRecognitionManager(
            engine="remote_api",
            remote_api_url="http://localhost:9090",
            remote_api_key="test-api-key",
        )
        self.assertTrue(manager._model_initialized)
        self.assertEqual(manager.remote_api_key, "test-api-key")
        # Verify the API key was sent in the request headers
        mock_get.assert_called_once_with(
            "http://localhost:9090",
            headers={"Authorization": "Bearer test-api-key"},
            timeout=5,
        )

    def test_remote_api_init_with_inference_endpoint(self):
        """Test remote API initialization with whisper.cpp server endpoint."""
        SpeechRecognitionManager = _import_manager()
        _setup_requests_get_ok()

        manager = SpeechRecognitionManager(
            engine="remote_api",
            remote_api_url="http://localhost:9090",
            remote_api_endpoint="/inference",
        )
        self.assertEqual(manager.remote_api_endpoint, "/inference")

    def test_remote_api_init_with_openai_endpoint(self):
        """Test remote API initialization with OpenAI compatible endpoint."""
        SpeechRecognitionManager = _import_manager()
        _setup_requests_get_ok()

        manager = SpeechRecognitionManager(
            engine="remote_api",
            remote_api_url="http://localhost:8080",
            remote_api_endpoint="/v1/audio/transcriptions",
        )
        self.assertEqual(manager.remote_api_endpoint, "/v1/audio/transcriptions")

    def test_model_ready_remote_api_initialized(self):
        """Test model_ready returns True for remote API when initialized."""
        SpeechRecognitionManager = _import_manager()
        _setup_requests_get_ok()

        manager = SpeechRecognitionManager(
            engine="remote_api",
            remote_api_url="http://localhost:9090",
        )
        # Should be available after initialization
        self.assertTrue(manager.model_ready)

    def test_model_ready_remote_api_not_initialized(self):
        """Test model_ready returns False when remote API not initialized."""
        SpeechRecognitionManager = _import_manager()
        manager = SpeechRecognitionManager(
            engine="remote_api",
            remote_api_url="",
        )
        # Should not be available without URL
        self.assertFalse(manager.model_ready)


class TestRemoteAPITranscription(unittest.TestCase):
    """Test cases for remote API transcription functionality."""

    def setUp(self):
        """Set up test fixtures."""
        SpeechRecognitionManager = _import_manager()
        _setup_requests_get_ok()

        self.manager = SpeechRecognitionManager(
            engine="remote_api",
            remote_api_url="http://localhost:9090",
            remote_api_key="test-key",
            remote_api_endpoint="/inference",
        )

    def test_transcribe_with_empty_buffer(self):
        """Test transcription with empty audio buffer."""
        result = self.manager._transcribe_with_remote_api([])
        self.assertEqual(result, "")

    def test_transcribe_with_no_url(self):
        """Test transcription when URL is not set."""
        self.manager.remote_api_url = ""
        result = self.manager._transcribe_with_remote_api([b"test"])
        self.assertEqual(result, "")

    def test_transcribe_with_openai_endpoint_success(self):
        """Test successful transcription via OpenAI endpoint."""
        from unittest.mock import patch

        with patch.object(self.manager, "_try_openai_api") as mock_openai:
            mock_openai.return_value = "test transcription"

            # Change endpoint to OpenAI
            self.manager.remote_api_endpoint = "/v1/audio/transcriptions"
            result = self.manager._transcribe_with_remote_api([b"test-audio-data"])

            self.assertEqual(result, "test transcription")

    def test_transcribe_with_whisper_cpp_server_endpoint_success(self):
        """Test successful transcription via whisper.cpp server endpoint."""
        from unittest.mock import patch

        with patch.object(self.manager, "_try_whispercpp_server_api") as mock_server:
            mock_server.return_value = "hello world"

            result = self.manager._transcribe_with_remote_api([b"audio-bytes"])

            self.assertEqual(result, "hello world")

    def test_transcribe_with_whispercpp_api_failing(self):
        """Test transcription returns empty string when whisper.cpp server API fails."""
        from unittest.mock import patch

        with patch.object(self.manager, "_try_whispercpp_server_api") as mock_server:
            mock_server.return_value = None

            result = self.manager._transcribe_with_remote_api([b"some-audio"])

            # Should return empty string when API returns None
            self.assertEqual(result, "")
            mock_server.assert_called_once()

    def test_transcribe_with_openai_api_failing(self):
        """Test transcription returns empty string when OpenAI API fails."""
        from unittest.mock import patch

        self.manager.remote_api_endpoint = "/v1/audio/transcriptions"
        with patch.object(self.manager, "_try_openai_api") as mock_openai:
            mock_openai.return_value = None

            result = self.manager._transcribe_with_remote_api([b"some-audio"])

            # Should return empty string when API returns None
            self.assertEqual(result, "")
            mock_openai.assert_called_once()

    def test_transcribe_with_language_en_us_conversion(self):
        """Test language code conversion from en-us to en."""
        from unittest.mock import patch

        with patch.object(self.manager, "_try_whispercpp_server_api") as mock_server:
            mock_server.return_value = "test"

            self.manager.language = "en-us"
            self.manager._transcribe_with_remote_api([b"audio"])

            # Should have been called with "en" (converted from "en-us")
            mock_server.assert_called_once_with(ANY, "en", ANY)

    def test_transcribe_with_language_auto(self):
        """Test with auto language detection."""
        from unittest.mock import patch

        with patch.object(self.manager, "_try_whispercpp_server_api") as mock_server:
            mock_server.return_value = "test"

            self.manager.language = "auto"
            self.manager._transcribe_with_remote_api([b"audio"])

            # Should pass None for auto detection
            mock_server.assert_called_once_with(ANY, None, ANY)


class TestOpenAIAPIFormat(unittest.TestCase):
    """Test cases for OpenAI compatible API format."""

    def setUp(self):
        """Set up test fixtures."""
        SpeechRecognitionManager = _import_manager()
        _setup_requests_get_ok()

        self.manager = SpeechRecognitionManager(
            engine="remote_api",
            remote_api_url="http://localhost:8080",
            remote_api_key="my-api-key",
            remote_api_endpoint="/v1/audio/transcriptions",
        )

    def test_try_openai_api_success(self):
        """Test successful transcription via OpenAI API format."""
        _setup_requests_post_ok({"text": "transcribed text"})

        result = self.manager._try_openai_api(b"wav-bytes", "en", {"Authorization": "Bearer key"})

        self.assertEqual(result, "transcribed text")

    def test_try_openai_api_with_404(self):
        """Test OpenAI API format returns None for 404."""
        _setup_requests_post_status(404)

        result = self.manager._try_openai_api(b"wav", "en", {})

        self.assertIsNone(result)

    def test_try_openai_api_connection_error(self):
        """Test OpenAI API handles connection errors gracefully."""
        _setup_requests_post_error(Exception("Connection refused"))

        result = self.manager._try_openai_api(b"wav", "en", {})

        self.assertIsNone(result)

    def test_try_openai_api_with_language(self):
        """Test OpenAI API includes language in request."""
        mock_post = _setup_requests_post_ok({"text": "result"})

        self.manager._try_openai_api(b"wav-bytes", "fr", {})

        # Check that language was included in the data
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        self.assertEqual(call_kwargs["data"]["language"], "fr")

    def test_try_openai_api_server_error(self):
        """Test OpenAI API handles 500 server error via raise_for_status."""
        _setup_requests_post_status(500, Exception("500 Server Error"))

        result = self.manager._try_openai_api(b"wav", "en", {})

        self.assertIsNone(result)

    def test_try_openai_api_auth_error(self):
        """Test OpenAI API handles 401 unauthorized via raise_for_status."""
        _setup_requests_post_status(401, Exception("401 Unauthorized"))

        result = self.manager._try_openai_api(b"wav", "en", {})

        self.assertIsNone(result)


class TestWhisperCppServerAPIFormat(unittest.TestCase):
    """Test cases for whisper.cpp server API format."""

    def setUp(self):
        """Set up test fixtures."""
        SpeechRecognitionManager = _import_manager()
        _setup_requests_get_ok()

        self.manager = SpeechRecognitionManager(
            engine="remote_api",
            remote_api_url="http://localhost:9090",
            remote_api_key="server-key",
            remote_api_endpoint="/inference",
        )

    def test_try_whispercpp_server_api_success(self):
        """Test successful transcription via whisper.cpp server API."""
        _setup_requests_post_ok({"text": "spoken words"})

        result = self.manager._try_whispercpp_server_api(
            b"audio-wav", "de", {"Authorization": "Bearer key"}
        )

        self.assertEqual(result, "spoken words")

    def test_try_whispercpp_server_api_404(self):
        """Test whisper.cpp server returns None for 404."""
        _setup_requests_post_status(404)

        result = self.manager._try_whispercpp_server_api(b"wav", "es", {})

        self.assertIsNone(result)

    def test_try_whispercpp_server_api_connection_error(self):
        """Test whisper.cpp server handles connection errors."""
        _setup_requests_post_error(Exception("Connection refused"))

        result = self.manager._try_whispercpp_server_api(b"wav", "es", {})

        self.assertIsNone(result)

    def test_try_whispercpp_server_api_server_error(self):
        """Test whisper.cpp server handles 500 error via raise_for_status."""
        _setup_requests_post_status(500, Exception("500 Server Error"))

        result = self.manager._try_whispercpp_server_api(b"wav", "en", {})

        self.assertIsNone(result)

    def test_try_whispercpp_server_api_auth_error(self):
        """Test whisper.cpp server handles 401 unauthorized via raise_for_status."""
        _setup_requests_post_status(401, Exception("401 Unauthorized"))

        result = self.manager._try_whispercpp_server_api(b"wav", "en", {})

        self.assertIsNone(result)


class TestRemoteAPIReconfiguration(unittest.TestCase):
    """Test cases for remote API settings updates."""

    def setUp(self):
        """Set up test fixtures."""
        SpeechRecognitionManager = _import_manager()
        _setup_requests_get_ok()

        self.manager = SpeechRecognitionManager(
            engine="remote_api",
            remote_api_url="http://localhost:9090",
        )

    def test_update_remote_api_url(self):
        """Test updating remote API URL via reconfigure triggers reinit."""
        _setup_requests_get_ok()

        self.manager.reconfigure(remote_api_url="https://new-server:9090")

        self.assertEqual(self.manager.remote_api_url, "https://new-server:9090")
        # Verify successful reinitialization after reconfigure
        self.assertTrue(self.manager._model_initialized)
        self.assertTrue(self.manager.model_ready)

    def test_update_remote_api_key(self):
        """Test updating remote API key via reconfigure."""
        self.manager.reconfigure(remote_api_key="new-secret-key")
        self.assertEqual(self.manager.remote_api_key, "new-secret-key")

    def test_update_remote_api_endpoint(self):
        """Test updating remote API endpoint via reconfigure."""
        self.manager.reconfigure(remote_api_endpoint="/v1/audio/transcriptions")
        self.assertEqual(self.manager.remote_api_endpoint, "/v1/audio/transcriptions")


if __name__ == "__main__":
    unittest.main()

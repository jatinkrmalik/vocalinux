"""
Tests for the logging_manager module.
"""

import logging
import os
import tempfile
import threading
import time
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


class TestLogRecord:
    """Tests for LogRecord class."""

    def test_init(self):
        """Test LogRecord initialization."""
        from vocalinux.ui.logging_manager import LogRecord

        timestamp = datetime.now()
        record = LogRecord(
            timestamp=timestamp,
            level="INFO",
            logger_name="test.module",
            message="Test message",
            module="test",
        )

        assert record.timestamp == timestamp
        assert record.level == "INFO"
        assert record.logger_name == "test.module"
        assert record.message == "Test message"
        assert record.module == "test"

    def test_init_default_module(self):
        """Test LogRecord initialization with default module."""
        from vocalinux.ui.logging_manager import LogRecord

        timestamp = datetime.now()
        record = LogRecord(
            timestamp=timestamp, level="DEBUG", logger_name="mylogger", message="Test"
        )

        assert record.module == ""

    def test_to_dict(self):
        """Test LogRecord to_dict method."""
        from vocalinux.ui.logging_manager import LogRecord

        timestamp = datetime(2024, 1, 15, 10, 30, 45, 123456)
        record = LogRecord(
            timestamp=timestamp,
            level="WARNING",
            logger_name="test.module",
            message="Warning message",
            module="test",
        )

        result = record.to_dict()

        assert result["timestamp"] == "2024-01-15T10:30:45.123456"
        assert result["level"] == "WARNING"
        assert result["logger_name"] == "test.module"
        assert result["message"] == "Warning message"
        assert result["module"] == "test"

    def test_str(self):
        """Test LogRecord string representation."""
        from vocalinux.ui.logging_manager import LogRecord

        timestamp = datetime(2024, 1, 15, 10, 30, 45, 123456)
        record = LogRecord(
            timestamp=timestamp,
            level="ERROR",
            logger_name="test.module",
            message="Error occurred",
            module="test",
        )

        result = str(record)

        assert "10:30:45.123" in result
        assert "ERROR" in result
        assert "test.module" in result
        assert "Error occurred" in result


class TestLoggingManager:
    """Tests for LoggingManager class."""

    @pytest.fixture
    def logging_manager(self):
        """Create a fresh LoggingManager for each test."""
        # Reset the global instance
        import vocalinux.ui.logging_manager as lm

        lm._logging_manager = None

        # Remove any existing handlers from root logger to avoid interference
        root_logger = logging.getLogger()
        handlers_to_remove = [h for h in root_logger.handlers if isinstance(h, lm.LoggingHandler)]
        for h in handlers_to_remove:
            root_logger.removeHandler(h)

        manager = lm.LoggingManager(max_records=100)
        yield manager

        # Cleanup: remove handler after test
        root_logger.removeHandler(manager.handler)

    def test_init(self, logging_manager):
        """Test LoggingManager initialization."""
        assert logging_manager.max_records == 100
        assert logging_manager.log_callbacks == []
        assert logging_manager.handler is not None

    def test_add_log_record(self, logging_manager):
        """Test adding a log record."""
        from vocalinux.ui.logging_manager import LogRecord

        record = LogRecord(
            timestamp=datetime.now(),
            level="INFO",
            logger_name="test",
            message="Test message",
        )

        logging_manager.add_log_record(record)

        # Account for the init log message and any others
        assert any(r.message == "Test message" for r in logging_manager.log_records)

    def test_add_log_record_trims_old_records(self, logging_manager):
        """Test that old records are trimmed when max_records is exceeded."""
        from vocalinux.ui.logging_manager import LogRecord

        logging_manager.max_records = 5

        for i in range(10):
            record = LogRecord(
                timestamp=datetime.now(),
                level="INFO",
                logger_name="test",
                message=f"Message {i}",
            )
            logging_manager.add_log_record(record)

        assert len(logging_manager.log_records) == 5
        # Should have the last 5 messages
        messages = [r.message for r in logging_manager.log_records]
        assert "Message 9" in messages
        assert "Message 5" in messages

    def test_add_log_record_notifies_callbacks(self, logging_manager):
        """Test that callbacks are notified when records are added."""
        from vocalinux.ui.logging_manager import LogRecord

        callback_records = []

        def callback(record):
            callback_records.append(record)

        logging_manager.register_callback(callback)

        record = LogRecord(
            timestamp=datetime.now(),
            level="INFO",
            logger_name="test",
            message="Callback test",
        )
        logging_manager.add_log_record(record)

        assert len(callback_records) >= 1
        assert any(r.message == "Callback test" for r in callback_records)

    def test_callback_error_does_not_break_logging(self, logging_manager):
        """Test that callback errors don't break logging."""
        from vocalinux.ui.logging_manager import LogRecord

        def bad_callback(record):
            raise ValueError("Callback error")

        logging_manager.register_callback(bad_callback)

        record = LogRecord(
            timestamp=datetime.now(),
            level="INFO",
            logger_name="test",
            message="Should still work",
        )

        # Should not raise
        logging_manager.add_log_record(record)
        assert any(r.message == "Should still work" for r in logging_manager.log_records)

    def test_register_callback(self, logging_manager):
        """Test callback registration."""

        def callback(record):
            pass

        logging_manager.register_callback(callback)

        assert callback in logging_manager.log_callbacks

    def test_unregister_callback(self, logging_manager):
        """Test callback unregistration."""

        def callback(record):
            pass

        logging_manager.register_callback(callback)
        logging_manager.unregister_callback(callback)

        assert callback not in logging_manager.log_callbacks

    def test_unregister_nonexistent_callback(self, logging_manager):
        """Test unregistering a callback that was never registered."""

        def callback(record):
            pass

        # Should not raise
        logging_manager.unregister_callback(callback)

    def test_get_logs_no_filter(self, logging_manager):
        """Test getting logs without filters."""
        from vocalinux.ui.logging_manager import LogRecord

        for i in range(5):
            record = LogRecord(
                timestamp=datetime.now(),
                level="INFO",
                logger_name="test",
                message=f"Message {i}",
            )
            logging_manager.add_log_record(record)

        logs = logging_manager.get_logs()

        assert len(logs) >= 5

    def test_get_logs_level_filter(self, logging_manager):
        """Test getting logs with level filter."""
        from vocalinux.ui.logging_manager import LogRecord

        logging_manager.log_records.clear()

        for level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            record = LogRecord(
                timestamp=datetime.now(),
                level=level,
                logger_name="test",
                message=f"{level} message",
            )
            logging_manager.add_log_record(record)

        error_logs = logging_manager.get_logs(level_filter="ERROR")

        assert len(error_logs) == 1
        assert error_logs[0].level == "ERROR"

    def test_get_logs_module_filter(self, logging_manager):
        """Test getting logs with module filter."""
        from vocalinux.ui.logging_manager import LogRecord

        logging_manager.log_records.clear()

        record1 = LogRecord(
            timestamp=datetime.now(),
            level="INFO",
            logger_name="vocalinux.ui.test",
            message="UI message",
        )
        record2 = LogRecord(
            timestamp=datetime.now(),
            level="INFO",
            logger_name="vocalinux.speech.test",
            message="Speech message",
        )
        logging_manager.add_log_record(record1)
        logging_manager.add_log_record(record2)

        ui_logs = logging_manager.get_logs(module_filter="ui")

        assert len(ui_logs) == 1
        assert "ui" in ui_logs[0].logger_name.lower()

    def test_get_logs_last_n(self, logging_manager):
        """Test getting last N logs."""
        from vocalinux.ui.logging_manager import LogRecord

        logging_manager.log_records.clear()

        for i in range(10):
            record = LogRecord(
                timestamp=datetime.now(),
                level="INFO",
                logger_name="test",
                message=f"Message {i}",
            )
            logging_manager.add_log_record(record)

        logs = logging_manager.get_logs(last_n=3)

        assert len(logs) == 3
        assert logs[-1].message == "Message 9"

    def test_export_logs(self, logging_manager):
        """Test exporting logs to a file."""
        from vocalinux.ui.logging_manager import LogRecord

        logging_manager.log_records.clear()

        record = LogRecord(
            timestamp=datetime.now(),
            level="INFO",
            logger_name="test",
            message="Export test message",
        )
        logging_manager.add_log_record(record)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            filepath = f.name

        try:
            result = logging_manager.export_logs(filepath)

            assert result is True
            assert os.path.exists(filepath)

            with open(filepath, "r") as f:
                content = f.read()

            assert "VocaLinux Log Export" in content
            assert "Export test message" in content
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    def test_export_logs_with_filters(self, logging_manager):
        """Test exporting logs with filters."""
        from vocalinux.ui.logging_manager import LogRecord

        logging_manager.log_records.clear()

        record = LogRecord(
            timestamp=datetime.now(),
            level="ERROR",
            logger_name="test.module",
            message="Error message",
        )
        logging_manager.add_log_record(record)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            filepath = f.name

        try:
            result = logging_manager.export_logs(
                filepath, level_filter="ERROR", module_filter="test"
            )

            assert result is True

            with open(filepath, "r") as f:
                content = f.read()

            assert "Level Filter: ERROR" in content
            assert "Module Filter: test" in content
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    def test_export_logs_failure(self, logging_manager):
        """Test export logs handles errors gracefully."""
        # Try to write to an invalid path
        result = logging_manager.export_logs("/nonexistent/directory/file.txt")

        assert result is False

    def test_clear_logs(self, logging_manager):
        """Test clearing logs."""
        from vocalinux.ui.logging_manager import LogRecord

        record = LogRecord(
            timestamp=datetime.now(),
            level="INFO",
            logger_name="test",
            message="Test message",
        )
        logging_manager.add_log_record(record)

        # Verify we have at least one record
        assert len(logging_manager.log_records) >= 1

        logging_manager.clear_logs()

        # clear_logs clears the list; the log message goes to root logger
        # which may or may not be captured depending on handler setup
        # Just verify clear() was called
        assert len(logging_manager.log_records) <= 1

    def test_get_log_stats_empty(self, logging_manager):
        """Test get_log_stats with no logs."""
        logging_manager.log_records.clear()

        stats = logging_manager.get_log_stats()

        assert stats["total"] == 0
        assert stats["by_level"] == {}
        assert stats["by_module"] == {}
        assert stats["oldest"] is None
        assert stats["newest"] is None

    def test_get_log_stats_with_records(self, logging_manager):
        """Test get_log_stats with records."""
        from vocalinux.ui.logging_manager import LogRecord

        logging_manager.log_records.clear()

        timestamp1 = datetime(2024, 1, 15, 10, 0, 0)
        timestamp2 = datetime(2024, 1, 15, 11, 0, 0)

        record1 = LogRecord(
            timestamp=timestamp1,
            level="INFO",
            logger_name="vocalinux.ui.test",
            message="Message 1",
        )
        record2 = LogRecord(
            timestamp=timestamp2,
            level="ERROR",
            logger_name="vocalinux.speech.test",
            message="Message 2",
        )
        logging_manager.add_log_record(record1)
        logging_manager.add_log_record(record2)

        stats = logging_manager.get_log_stats()

        assert stats["total"] == 2
        assert stats["by_level"]["INFO"] == 1
        assert stats["by_level"]["ERROR"] == 1
        assert "vocalinux" in stats["by_module"]
        assert stats["oldest"] == timestamp1
        assert stats["newest"] == timestamp2

    def test_get_log_stats_module_without_dot(self, logging_manager):
        """Test get_log_stats with logger name without dots."""
        from vocalinux.ui.logging_manager import LogRecord

        logging_manager.log_records.clear()

        record = LogRecord(
            timestamp=datetime.now(),
            level="INFO",
            logger_name="simplelogger",
            message="Message",
        )
        logging_manager.add_log_record(record)

        stats = logging_manager.get_log_stats()

        assert "simplelogger" in stats["by_module"]


class TestLoggingHandler:
    """Tests for LoggingHandler class."""

    @pytest.fixture
    def handler_setup(self):
        """Set up a LoggingHandler for testing."""
        import vocalinux.ui.logging_manager as lm

        lm._logging_manager = None

        # Create a minimal manager
        manager = MagicMock()
        manager.add_log_record = MagicMock()

        handler = lm.LoggingHandler(manager)
        yield handler, manager

    def test_emit(self, handler_setup):
        """Test emit method."""
        handler, manager = handler_setup

        log_record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        handler.emit(log_record)

        manager.add_log_record.assert_called_once()
        call_args = manager.add_log_record.call_args[0][0]
        assert call_args.level == "INFO"
        assert call_args.logger_name == "test.logger"
        assert call_args.message == "Test message"

    def test_emit_prevents_recursion(self, handler_setup):
        """Test that emit prevents recursive calls."""
        handler, manager = handler_setup

        # Simulate already emitting
        handler._emitting = True

        log_record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        handler.emit(log_record)

        # Should not have called add_log_record due to recursion prevention
        manager.add_log_record.assert_not_called()

    def test_emit_handles_errors(self, handler_setup):
        """Test that emit handles errors gracefully."""
        handler, manager = handler_setup
        manager.add_log_record.side_effect = Exception("Test error")

        log_record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        with patch.object(handler, "handleError") as mock_handle_error:
            handler.emit(log_record)
            mock_handle_error.assert_called_once()

        # _emitting should be reset even after error
        assert handler._emitting is False


class TestGlobalFunctions:
    """Tests for module-level functions."""

    def test_get_logging_manager_creates_instance(self):
        """Test that get_logging_manager creates instance if needed."""
        import vocalinux.ui.logging_manager as lm

        # Reset global
        lm._logging_manager = None

        # Remove any existing handlers
        root_logger = logging.getLogger()
        handlers_to_remove = [h for h in root_logger.handlers if isinstance(h, lm.LoggingHandler)]
        for h in handlers_to_remove:
            root_logger.removeHandler(h)

        manager = lm.get_logging_manager()

        assert manager is not None
        assert isinstance(manager, lm.LoggingManager)

        # Cleanup
        root_logger.removeHandler(manager.handler)

    def test_get_logging_manager_returns_same_instance(self):
        """Test that get_logging_manager returns the same instance."""
        import vocalinux.ui.logging_manager as lm

        # Reset global
        lm._logging_manager = None

        # Remove any existing handlers
        root_logger = logging.getLogger()
        handlers_to_remove = [h for h in root_logger.handlers if isinstance(h, lm.LoggingHandler)]
        for h in handlers_to_remove:
            root_logger.removeHandler(h)

        manager1 = lm.get_logging_manager()
        manager2 = lm.get_logging_manager()

        assert manager1 is manager2

        # Cleanup
        root_logger.removeHandler(manager1.handler)

    def test_initialize_logging(self):
        """Test initialize_logging function."""
        import vocalinux.ui.logging_manager as lm

        # Reset global
        lm._logging_manager = None

        # Remove any existing handlers
        root_logger = logging.getLogger()
        handlers_to_remove = [h for h in root_logger.handlers if isinstance(h, lm.LoggingHandler)]
        for h in handlers_to_remove:
            root_logger.removeHandler(h)

        lm.initialize_logging()

        assert lm._logging_manager is not None

        # Cleanup
        root_logger.removeHandler(lm._logging_manager.handler)

    def test_initialize_logging_does_not_recreate(self):
        """Test that initialize_logging doesn't recreate existing manager."""
        import vocalinux.ui.logging_manager as lm

        # Reset global
        lm._logging_manager = None

        # Remove any existing handlers
        root_logger = logging.getLogger()
        handlers_to_remove = [h for h in root_logger.handlers if isinstance(h, lm.LoggingHandler)]
        for h in handlers_to_remove:
            root_logger.removeHandler(h)

        lm.initialize_logging()
        first_manager = lm._logging_manager

        lm.initialize_logging()

        assert lm._logging_manager is first_manager

        # Cleanup
        root_logger.removeHandler(first_manager.handler)


class TestThreadSafety:
    """Tests for thread safety of LoggingManager."""

    def test_concurrent_add_log_record(self):
        """Test that adding records from multiple threads is thread-safe."""
        import vocalinux.ui.logging_manager as lm

        # Reset global
        lm._logging_manager = None

        # Remove any existing handlers
        root_logger = logging.getLogger()
        handlers_to_remove = [h for h in root_logger.handlers if isinstance(h, lm.LoggingHandler)]
        for h in handlers_to_remove:
            root_logger.removeHandler(h)

        manager = lm.LoggingManager(max_records=1000)

        def add_records(thread_id):
            for i in range(100):
                record = lm.LogRecord(
                    timestamp=datetime.now(),
                    level="INFO",
                    logger_name=f"thread_{thread_id}",
                    message=f"Message {i}",
                )
                manager.add_log_record(record)

        threads = [threading.Thread(target=add_records, args=(i,)) for i in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have records from all threads (plus any init messages)
        assert len(manager.log_records) >= 500

        # Cleanup
        root_logger.removeHandler(manager.handler)

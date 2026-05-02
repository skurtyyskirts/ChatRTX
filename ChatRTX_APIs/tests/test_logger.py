import logging
import os
import pytest
from ChatRTX.logger import ChatRTXLogger


@pytest.fixture(autouse=True)
def reset_logger_singleton():
    """Reset the ChatRTXLogger singleton and clear all handlers between tests."""
    ChatRTXLogger._instance = None
    yield
    # Close and remove handlers from the underlying logging.Logger so they
    # don't accumulate across tests (the logging module caches loggers globally).
    underlying = logging.getLogger("[ChatRTX]")
    for handler in underlying.handlers[:]:
        handler.close()
        underlying.removeHandler(handler)
    ChatRTXLogger._instance = None


class TestChatRTXLoggerSingleton:
    def test_returns_same_instance(self):
        a = ChatRTXLogger(log_level=logging.INFO)
        b = ChatRTXLogger(log_level=logging.DEBUG)
        assert a is b

    def test_get_logger_returns_logger_instance(self):
        ChatRTXLogger(log_level=logging.INFO)
        logger = ChatRTXLogger.get_logger()
        assert isinstance(logger, logging.Logger)

    def test_logger_name(self):
        ChatRTXLogger(log_level=logging.INFO)
        logger = ChatRTXLogger.get_logger()
        assert "[ChatRTX]" in logger.name


class TestChatRTXLoggerLevels:
    def test_set_log_level_info(self):
        ChatRTXLogger(log_level=logging.DEBUG)
        ChatRTXLogger.set_log_level(logging.INFO)
        logger = ChatRTXLogger.get_logger()
        assert logger.level == logging.INFO

    def test_set_log_level_warning(self):
        ChatRTXLogger(log_level=logging.DEBUG)
        ChatRTXLogger.set_log_level(logging.WARNING)
        logger = ChatRTXLogger.get_logger()
        assert logger.level == logging.WARNING

    def test_set_verbose_mode_true(self):
        ChatRTXLogger(log_level=logging.INFO)
        ChatRTXLogger.set_verbose_mode(True)
        logger = ChatRTXLogger.get_logger()
        assert logger.level == logging.DEBUG

    def test_set_verbose_mode_false(self):
        ChatRTXLogger(log_level=logging.DEBUG)
        ChatRTXLogger.set_verbose_mode(False)
        logger = ChatRTXLogger.get_logger()
        assert logger.level == logging.INFO


class TestChatRTXLoggerFileHandler:
    def test_creates_log_file(self, tmp_path):
        log_file = str(tmp_path / "test.log")
        ChatRTXLogger(log_level=logging.INFO, log_file=log_file)
        assert os.path.exists(log_file)

    def test_creates_log_directory(self, tmp_path):
        log_dir = tmp_path / "logs" / "subdir"
        log_file = str(log_dir / "app.log")
        ChatRTXLogger(log_level=logging.INFO, log_file=log_file)
        assert os.path.exists(log_file)

    def test_logger_writes_to_file(self, tmp_path):
        log_file = str(tmp_path / "output.log")
        ChatRTXLogger(log_level=logging.DEBUG, log_file=log_file)
        logger = ChatRTXLogger.get_logger()
        logger.info("test message written to file")
        with open(log_file) as f:
            content = f.read()
        assert "test message written to file" in content

    def test_bare_filename_does_not_crash(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ChatRTXLogger(log_level=logging.INFO, log_file="ChatRTX.log")
        assert os.path.exists(tmp_path / "ChatRTX.log")

# tests/test_logger.py
# Tests for ChatRTXLogger — pure Python, no GPU required.

import sys, os, logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ChatRTX_APIs"))

import pytest
from ChatRTX.logger import ChatRTXLogger


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the singleton between tests."""
    ChatRTXLogger._instance = None
    yield
    ChatRTXLogger._instance = None


class TestChatRTXLoggerSingleton:
    def test_same_instance_returned(self):
        a = ChatRTXLogger(log_level=logging.WARNING)
        b = ChatRTXLogger(log_level=logging.WARNING)
        assert a is b

    def test_get_logger_returns_logger_instance(self):
        ChatRTXLogger(log_level=logging.WARNING)
        logger = ChatRTXLogger.get_logger()
        assert isinstance(logger, logging.Logger)

    def test_logger_name_contains_chatrtx(self):
        ChatRTXLogger(log_level=logging.WARNING)
        logger = ChatRTXLogger.get_logger()
        assert "ChatRTX" in logger.name


class TestChatRTXLoggerLevels:
    def test_set_log_level_debug(self):
        ChatRTXLogger(log_level=logging.WARNING)
        ChatRTXLogger.set_log_level(logging.DEBUG)
        logger = ChatRTXLogger.get_logger()
        assert logger.level == logging.DEBUG

    def test_set_log_level_error(self):
        ChatRTXLogger(log_level=logging.WARNING)
        ChatRTXLogger.set_log_level(logging.ERROR)
        logger = ChatRTXLogger.get_logger()
        assert logger.level == logging.ERROR

    def test_verbose_mode_sets_debug(self):
        ChatRTXLogger(log_level=logging.WARNING)
        ChatRTXLogger.set_verbose_mode(True)
        logger = ChatRTXLogger.get_logger()
        assert logger.level == logging.DEBUG

    def test_verbose_mode_off_sets_info(self):
        ChatRTXLogger(log_level=logging.DEBUG)
        ChatRTXLogger.set_verbose_mode(False)
        logger = ChatRTXLogger.get_logger()
        assert logger.level == logging.INFO


class TestChatRTXLoggerFileHandler:
    def test_file_handler_created(self, tmp_path):
        log_file = str(tmp_path / "test.log")
        ChatRTXLogger(log_level=logging.DEBUG, log_file=log_file)
        logger = ChatRTXLogger.get_logger()
        handler_types = [type(h).__name__ for h in logger.handlers]
        assert "RotatingFileHandler" in handler_types

    def test_log_file_created(self, tmp_path):
        log_file = str(tmp_path / "chatrtx.log")
        ChatRTXLogger(log_level=logging.DEBUG, log_file=log_file)
        assert os.path.exists(log_file)

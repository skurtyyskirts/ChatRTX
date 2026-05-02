import sys
from unittest.mock import MagicMock, patch

# Mock modules that are not available or would fail on Linux/sandbox
mock_modules = [
    'configuration',
    'ChatRTX.chatrtx',
    'ChatRTX.chatrtx_rag',
    'ChatRTX.logger',
    'ChatRTX.model_manager.model_manager',
    'ResponseUtility',
    'pynvml',
    'ChatRTX.inference.trtllm.whisper.trt_whisper',
    'ChatRTX.inference.trtllm.whisper.whisper_utils'
]
for module in mock_modules:
    sys.modules[module] = MagicMock()

import pytest
from backend import Backend, Mode

@pytest.fixture
def mock_backend():
    with patch('backend.Configuration'), \
         patch('backend.ChatRTXLogger'), \
         patch('backend.ModelManager'):
        # Mocking the configuration and its expand_programdata_path method
        with patch('backend.Configuration.get_config', return_value='fake/path'):
            backend = Backend(model_setup_dir="/fake/dir")
            # Mocking attributes that are initialized in __init__ or used in methods
            backend.chatrtx = MagicMock()
            backend._logger = MagicMock()
            return backend

def test_generate_query_engine_clip_success(mock_backend):
    mock_backend.active_model = Backend.CLIP_MODEL
    mock_backend.chatrtx.generate_clip_engine.return_value = True

    result = mock_backend.generate_query_engine("/data/dir")

    assert result is True
    mock_backend.chatrtx.generate_clip_engine.assert_called_once_with("/data/dir")

def test_generate_query_engine_clip_failure(mock_backend):
    mock_backend.active_model = Backend.CLIP_MODEL
    mock_backend.chatrtx.generate_clip_engine.side_effect = Exception("CLIP error")

    result = mock_backend.generate_query_engine("/data/dir")

    assert result is False
    mock_backend._logger.error.assert_called()

def test_generate_query_engine_ai_mode_raises_error(mock_backend):
    mock_backend.active_model = "not_clip"
    mock_backend.chatrtx_mode = Mode.AI

    with pytest.raises(ValueError, match="ChatRTX Mode must be set to RAG"):
        mock_backend.generate_query_engine("/data/dir")

def test_generate_query_engine_rag_success(mock_backend):
    mock_backend.active_model = "some_llm"
    mock_backend.chatrtx_mode = Mode.RAG
    mock_backend.chatrtx.generate_query_engine.return_value = "fake_engine"

    result = mock_backend.generate_query_engine("/data/dir")

    assert result is True
    assert mock_backend.rag_engine == "fake_engine"
    assert mock_backend.current_data_dir == "/data/dir"
    mock_backend.chatrtx.generate_query_engine.assert_called_once_with("/data/dir", streaming=True)

def test_generate_query_engine_rag_failure(mock_backend):
    mock_backend.active_model = "some_llm"
    mock_backend.chatrtx_mode = Mode.RAG
    mock_backend.chatrtx.generate_query_engine.side_effect = Exception("RAG error")

    result = mock_backend.generate_query_engine("/data/dir")

    assert result is False
    mock_backend._logger.error.assert_called()

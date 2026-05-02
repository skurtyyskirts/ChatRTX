import sys
import types
from unittest.mock import MagicMock, patch
import pytest

class MockModule(types.ModuleType):
    def __init__(self, name):
        super().__init__(name)
        self.__path__ = []

    def __getattr__(self, name):
        return MagicMock()

def create_mock_module(name):
    mock = MockModule(name)
    sys.modules[name] = mock
    return mock

# The most robust way to inject a deep mock hierarchy without touching __import__
# and catching every dynamic subpackage
class DynamicMockFinder:
    def __init__(self, mocked_prefixes):
        self.mocked_prefixes = mocked_prefixes

    def find_spec(self, fullname, path, target=None):
        should_mock = False
        for prefix in self.mocked_prefixes:
            if fullname == prefix or fullname.startswith(prefix + '.'):
                should_mock = True
                break

        if should_mock:
            from importlib.machinery import ModuleSpec
            class MockLoader:
                def create_module(self, spec):
                    return MockModule(spec.name)
                def exec_module(self, module):
                    pass
            return ModuleSpec(fullname, MockLoader())
        return None

sys.meta_path.insert(0, DynamicMockFinder([
    'pynvml',
    'torch',
    'tensorrt_llm',
    'transformers',
    'tensorrt',
    'llama_index',
    'ngcsdk',
    'requests',
    'tqdm',
    'typing_extensions',
    'numpy',
    'PIL',
    'open_clip',
    'faiss',
    'huggingface_hub',
    'win32event',
    'win32api',
    'winerror',
    'ChatRTX.inference.trtllm.whisper.trt_whisper',
    'ChatRTX.inference.trtllm.whisper.whisper_utils'
]))

import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'ChatRTX_APIs')))

from backend import Backend, Mode

def test_chatrtx_ai_mode_exception():
    with patch('backend.Configuration'), patch('backend.ChatRTXLogger'), patch('backend.ModelManager'):
        backend = Backend('/mock/dir')
        backend.active_model = 'mock_model'
        # chatrtx_mode is assigned inside ChatRTX method as: self.chatrtx_mode = chatrtx_mode
        # so it will be Mode.AI

        # The method is literally named ChatRTX in the Backend class!
        with patch('backend.ChatRTX') as MockChatRTX:
            MockChatRTX.side_effect = Exception("Test exception")

            result = backend.ChatRTX(Mode.AI)

            assert result is False
            backend._logger.error.assert_called_once()

def test_chatrtx_ai_mode_init_llm_model_exception():
    with patch('backend.Configuration'), patch('backend.ChatRTXLogger'), patch('backend.ModelManager'):
        backend = Backend('/mock/dir')
        backend.active_model = 'mock_model'

        with patch('backend.ChatRTX') as MockChatRTX:
            mock_instance = MagicMock()
            mock_instance.init_llm_model.side_effect = Exception("Test exception")
            MockChatRTX.return_value = mock_instance

            result = backend.ChatRTX(Mode.AI)

            assert result is False
            backend._logger.error.assert_called_once()

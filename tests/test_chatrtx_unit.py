# tests/test_chatrtx_unit.py
# Unit tests for ChatRTX class logic that does NOT require GPU/TRT engines.
# Heavy inference calls are mocked with unittest.mock.

import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ChatRTX_APIs"))

import pytest
from unittest.mock import MagicMock, patch


# ── helpers ───────────────────────────────────────────────────────────────────

def make_model_info(model_id="llama-2-13b-chat",
                    engine="llama_float16_tp1_rank0.engine",
                    tokenizer_dir="tokenizer_local_dir",
                    backend_name="LlamaForCausalLM",
                    max_new_tokens=512,
                    max_input_token=4096,
                    temperature=0.1):
    return {
        "id": model_id,
        "metadata": {
            "engine": engine,
            "model_name": backend_name,
            "max_new_tokens": max_new_tokens,
            "max_input_token": max_input_token,
            "temperature": temperature,
        },
        "prerequisite": {
            "tokenizer_local_dir": tokenizer_dir
        }
    }


@pytest.fixture
def app_config(tmp_path):
    cfg = {
        "use_py_session": False,
        "add_special_tokens": True,
        "trtLlm_debug_mode": False
    }
    p = tmp_path / "app_config.json"
    p.write_text(json.dumps(cfg), encoding="utf-8")
    return str(p)


@pytest.fixture
def chatrtx_instance(tmp_path, app_config):
    """Return a ChatRTX instance with mocked heavy deps."""
    models_info = [make_model_info()]

    with patch("ChatRTX.chatrtx.TrtLlm"), \
         patch("ChatRTX.chatrtx.ClipInference"), \
         patch("ChatRTX.chatrtx.ChatRTXLogger") as mock_logger_cls:

        mock_logger = MagicMock()
        mock_logger_cls.return_value = mock_logger
        mock_logger_cls.get_logger.return_value = mock_logger

        from ChatRTX.chatrtx import ChatRTX

        # Patch the app_config path inside the module
        with patch.object(ChatRTX, "_load_config", return_value={
            "use_py_session": False,
            "add_special_tokens": True,
            "trtLlm_debug_mode": False
        }):
            instance = ChatRTX(models_info, str(tmp_path))
            instance._logger = mock_logger
            yield instance


# ── _load_config ──────────────────────────────────────────────────────────────

class TestLoadConfig:
    def test_loads_valid_json(self, tmp_path):
        from ChatRTX.chatrtx import ChatRTX
        models_info = [make_model_info()]

        cfg_data = {"use_py_session": False, "add_special_tokens": True, "trtLlm_debug_mode": False}
        cfg_file = tmp_path / "app_config.json"
        cfg_file.write_text(json.dumps(cfg_data), encoding="utf-8")

        with patch("ChatRTX.chatrtx.TrtLlm"), \
             patch("ChatRTX.chatrtx.ClipInference"), \
             patch("ChatRTX.chatrtx.ChatRTXLogger") as ml:
            ml.get_logger.return_value = MagicMock()
            # override os.path.join to return our test config
            import ChatRTX.chatrtx as mod
            real_join = os.path.join
            with patch("os.path.join", side_effect=lambda *a: str(cfg_file) if "app_config.json" in str(a) else real_join(*a)):
                inst = ChatRTX(models_info, str(tmp_path))
            result = inst._load_config(str(cfg_file))
        assert result["use_py_session"] is False

    def test_raises_for_missing_file(self, chatrtx_instance):
        with pytest.raises(FileNotFoundError):
            chatrtx_instance._load_config("/nonexistent/path/config.json")

    def test_raises_for_invalid_json(self, chatrtx_instance, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not json}", encoding="utf-8")
        with pytest.raises(ValueError):
            chatrtx_instance._load_config(str(bad))


# ── generate_response guards ──────────────────────────────────────────────────

class TestGenerateResponseGuards:
    def test_raises_when_no_model_loaded(self, chatrtx_instance):
        chatrtx_instance._llm = None
        with pytest.raises(Exception, match="No model is loaded"):
            chatrtx_instance.generate_response("hello")

    def test_raises_stream_when_no_model_loaded(self, chatrtx_instance):
        chatrtx_instance._llm = None
        with pytest.raises(Exception, match="No model is loaded"):
            list(chatrtx_instance.generate_stream_response("hello"))


# ── init_llm_model error paths ────────────────────────────────────────────────

class TestInitLlmModelErrors:
    def test_returns_false_for_unknown_model_id(self, chatrtx_instance):
        result = chatrtx_instance.init_llm_model("nonexistent-model-id")
        assert result is False

    def test_returns_false_for_unsupported_backend(self, chatrtx_instance):
        result = chatrtx_instance.init_llm_model("llama-2-13b-chat", backend="PYTORCH")
        assert result is False


# ── generate_response with mocked LLM ────────────────────────────────────────

class TestGenerateResponseWithMockLLM:
    def test_returns_response_string(self, chatrtx_instance):
        mock_llm = MagicMock()
        mock_llm.get_model_name.return_value = "LlamaForCausalLM"
        mock_llm.complete.return_value = MagicMock(text="Hello, world!")
        chatrtx_instance._llm = mock_llm

        result = chatrtx_instance.generate_response("Hi")
        assert result is not None
        mock_llm.complete.assert_called_once()

    def test_stream_response_yields_tokens(self, chatrtx_instance):
        mock_llm = MagicMock()
        mock_llm.get_model_name.return_value = "LlamaForCausalLM"
        mock_llm.stream_complete.return_value = iter(["tok1", "tok2", "tok3"])
        chatrtx_instance._llm = mock_llm

        tokens = list(chatrtx_instance.generate_stream_response("Hi"))
        assert tokens == ["tok1", "tok2", "tok3"]


# ── unload_llm ────────────────────────────────────────────────────────────────

class TestUnloadLlm:
    def test_unload_sets_llm_to_none(self, chatrtx_instance):
        mock_llm = MagicMock()
        chatrtx_instance._llm = mock_llm
        chatrtx_instance.unload_llm()
        assert chatrtx_instance._llm is None
        mock_llm.unload_llm.assert_called_once()

    def test_unload_when_no_llm_does_nothing(self, chatrtx_instance):
        chatrtx_instance._llm = None
        chatrtx_instance.unload_llm()  # should not raise

    def test_unload_raises_if_unload_fails(self, chatrtx_instance):
        mock_llm = MagicMock()
        mock_llm.unload_llm.side_effect = RuntimeError("driver crash")
        chatrtx_instance._llm = mock_llm
        with pytest.raises(Exception, match="Failed to unload"):
            chatrtx_instance.unload_llm()

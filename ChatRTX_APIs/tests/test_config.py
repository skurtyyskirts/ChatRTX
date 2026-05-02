import json
import os
import pytest
from ChatRTX.model_manager.config import Config


@pytest.fixture
def config_file(tmp_path):
    data = {
        "models": {
            "selected": "mistral_7b",
            "supported": [
                {"id": "mistral_7b", "name": "Mistral 7B", "downloaded": False}
            ]
        },
        "dataset": {
            "selected": "directory",
            "path": "/some/path"
        }
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


@pytest.fixture
def config(config_file):
    return Config(config_file)


class TestGetConfig:
    def test_returns_full_config_for_empty_key(self, config):
        result = config.get_config("")
        assert "models" in result
        assert "dataset" in result

    def test_returns_top_level_key(self, config):
        result = config.get_config("models")
        assert "selected" in result
        assert result["selected"] == "mistral_7b"

    def test_returns_nested_key(self, config):
        result = config.get_config("models/selected")
        assert result == "mistral_7b"

    def test_returns_none_for_missing_key(self, config):
        result = config.get_config("nonexistent/key")
        assert result is None

    def test_returns_list_value(self, config):
        result = config.get_config("models/supported")
        assert isinstance(result, list)
        assert len(result) == 1

    def test_deep_nested_key(self, config):
        result = config.get_config("dataset/selected")
        assert result == "directory"


class TestWriteDefaultConfig:
    def test_writes_scalar_value(self, config, config_file):
        config.write_default_config("models/selected", "llama2_13b")
        fresh = Config(config_file)
        assert fresh.get_config("models/selected") == "llama2_13b"

    def test_writes_nested_new_key(self, config, config_file):
        config.write_default_config("models/version", "0.4.0")
        fresh = Config(config_file)
        assert fresh.get_config("models/version") == "0.4.0"

    def test_writes_list_value(self, config, config_file):
        new_list = [{"id": "new_model", "name": "New"}]
        config.write_default_config("models/supported", new_list)
        fresh = Config(config_file)
        result = fresh.get_config("models/supported")
        assert result[0]["id"] == "new_model"

    def test_write_then_read_roundtrip(self, config, config_file):
        config.write_default_config("dataset/path", "/new/data/path")
        fresh = Config(config_file)
        assert fresh.get_config("dataset/path") == "/new/data/path"


class TestGetConfigFromFile:
    def test_reads_key_from_explicit_file(self, config, config_file):
        result = config.get_config_from_file("models/selected", config_file)
        assert result == "mistral_7b"

    def test_returns_none_for_empty_key(self, config, config_file):
        result = config.get_config_from_file("", config_file)
        assert result is None

    def test_returns_none_for_none_file(self, config):
        result = config.get_config_from_file("models/selected", None)
        assert result is None

    def test_returns_none_for_missing_key_in_file(self, config, config_file):
        result = config.get_config_from_file("missing/key", config_file)
        assert result is None


class TestConfigRobustness:
    def test_handles_empty_json_file(self, tmp_path):
        path = tmp_path / "empty.json"
        path.write_text("{}", encoding="utf-8")
        cfg = Config(str(path))
        assert cfg.get_config("anything") is None

    def test_handles_missing_file_gracefully(self, tmp_path):
        path = tmp_path / "missing.json"
        cfg = Config(str(path))
        assert cfg.get_config("key") is None

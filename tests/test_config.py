# tests/test_config.py
# Tests for Config class in model_manager — pure Python, no GPU required.

import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ChatRTX_APIs"))

import pytest
from ChatRTX.model_manager.config import Config


@pytest.fixture
def config_file(tmp_path):
    data = {
        "version": "1.0",
        "models": {
            "llama": {"max_tokens": 512},
            "gemma": {"max_tokens": 1024}
        },
        "flags": {
            "use_py_session": True,
            "add_special_tokens": False
        }
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


@pytest.fixture
def cfg(config_file):
    return Config(config_file)


# ── get_config ────────────────────────────────────────────────────────────────

class TestGetConfig:
    def test_returns_full_config_for_empty_key(self, cfg):
        result = cfg.get_config("")
        assert isinstance(result, dict)
        assert "version" in result

    def test_returns_full_config_for_none_key(self, cfg):
        result = cfg.get_config(None)
        assert isinstance(result, dict)

    def test_top_level_key(self, cfg):
        assert cfg.get_config("version") == "1.0"

    def test_nested_key_slash_separated(self, cfg):
        assert cfg.get_config("models/llama/max_tokens") == 512

    def test_nested_key_two_levels(self, cfg):
        result = cfg.get_config("flags/use_py_session")
        assert result is True

    def test_missing_key_returns_none(self, cfg):
        assert cfg.get_config("nonexistent") is None

    def test_missing_nested_key_returns_none(self, cfg):
        assert cfg.get_config("models/unknown/max_tokens") is None


# ── get_config_from_file ──────────────────────────────────────────────────────

class TestGetConfigFromFile:
    def test_reads_key_from_separate_file(self, cfg, tmp_path):
        extra = {"setting": {"value": 42}}
        extra_path = str(tmp_path / "extra.json")
        with open(extra_path, "w") as f:
            json.dump(extra, f)
        assert cfg.get_config_from_file("setting/value", extra_path) == 42

    def test_returns_none_for_empty_file_path(self, cfg):
        assert cfg.get_config_from_file("version", "") is None

    def test_returns_none_for_none_file_path(self, cfg):
        assert cfg.get_config_from_file("version", None) is None

    def test_returns_none_for_empty_key(self, cfg, config_file):
        assert cfg.get_config_from_file("", config_file) is None


# ── write_default_config ──────────────────────────────────────────────────────

class TestWriteDefaultConfig:
    def test_writes_new_top_level_key(self, cfg, config_file):
        cfg.write_default_config("new_key", "new_value")
        with open(config_file, "r") as f:
            data = json.load(f)
        assert data["new_key"] == "new_value"

    def test_writes_nested_key(self, cfg, config_file):
        cfg.write_default_config("models/llama/max_tokens", 999)
        with open(config_file, "r") as f:
            data = json.load(f)
        assert data["models"]["llama"]["max_tokens"] == 999

    def test_overwrites_existing_key(self, cfg, config_file):
        cfg.write_default_config("version", "2.0")
        assert cfg.get_config("version") == "2.0"

    def test_creates_intermediate_keys(self, cfg, config_file):
        cfg.write_default_config("deep/nested/key", True)
        with open(config_file, "r") as f:
            data = json.load(f)
        assert data["deep"]["nested"]["key"] is True


# ── edge cases ────────────────────────────────────────────────────────────────

class TestConfigEdgeCases:
    def test_invalid_json_file_returns_empty(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json", encoding="utf-8")
        cfg = Config(str(bad))
        assert cfg.get_config("anything") is None

    def test_missing_file_returns_empty(self, tmp_path):
        cfg = Config(str(tmp_path / "missing.json"))
        assert cfg.get_config("anything") is None

    def test_empty_json_file(self, tmp_path):
        empty = tmp_path / "empty.json"
        empty.write_text("{}", encoding="utf-8")
        cfg = Config(str(empty))
        assert cfg.get_config("key") is None

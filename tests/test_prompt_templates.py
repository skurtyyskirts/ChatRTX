# tests/test_prompt_templates.py
# Tests for LLMPromptTemplate — pure Python, no GPU required.

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ChatRTX_APIs"))

import pytest
from ChatRTX.llm_prompt_templates import LLMPromptTemplate


@pytest.fixture
def tpl():
    return LLMPromptTemplate()


# ── model_default_template ────────────────────────────────────────────────────

class TestModelDefaultTemplate:
    def test_llama2_wraps_query_in_inst_tags(self, tpl):
        result = tpl.model_default_template("LlamaForCausalLM", "Hello?")
        assert "[INST]" in result
        assert "[/INST]" in result
        assert "Hello?" in result

    def test_llama2_starts_with_bos(self, tpl):
        result = tpl.model_default_template("LlamaForCausalLM", "test")
        assert result.startswith("<s>")

    def test_gemma_wraps_user_turn(self, tpl):
        result = tpl.model_default_template("GemmaForCausalLM", "Hi there")
        assert "<start_of_turn>user" in result
        assert "<start_of_turn>model" in result
        assert "Hi there" in result

    def test_chatglm_wraps_with_system_and_user(self, tpl):
        result = tpl.model_default_template("ChatGLMForCausalLM", "Explain AI")
        assert "<|user|>" in result
        assert "<|assistant|>" in result
        assert "Explain AI" in result

    def test_unknown_model_returns_raw_query(self, tpl):
        result = tpl.model_default_template("UnknownModel", "raw query")
        assert result == "raw query"

    def test_empty_query_llama2(self, tpl):
        result = tpl.model_default_template("LlamaForCausalLM", "")
        assert "[INST]" in result
        assert "[/INST]" in result

    def test_multiline_query_preserved(self, tpl):
        q = "Line one\nLine two"
        result = tpl.model_default_template("GemmaForCausalLM", q)
        assert "Line one" in result
        assert "Line two" in result


# ── model_context_template ────────────────────────────────────────────────────

class TestModelContextTemplate:
    def test_llama_context_returns_callable(self, tpl):
        fn = tpl.model_context_template("LlamaForCausalLM")
        assert callable(fn)

    def test_gemma_context_returns_callable(self, tpl):
        fn = tpl.model_context_template("GemmaForCausalLM")
        assert callable(fn)

    def test_chatglm_context_returns_callable(self, tpl):
        fn = tpl.model_context_template("ChatGLMForCausalLM")
        assert callable(fn)

    def test_llama_context_output_contains_sys_tags(self, tpl):
        fn = tpl.model_context_template("LlamaForCausalLM")
        result = fn("some completion")
        assert "<<SYS>>" in result
        assert "<</SYS>>" in result

    def test_gemma_context_output_structure(self, tpl):
        fn = tpl.model_context_template("GemmaForCausalLM")
        result = fn("some completion")
        assert "<start_of_turn>user" in result
        assert "some completion" in result

    def test_chatglm_context_uses_system_prompt(self, tpl):
        fn = tpl.model_context_template("ChatGLMForCausalLM")
        result = fn("my message", system_prompt="Be brief.")
        assert "Be brief." in result
        assert "my message" in result

    def test_chatglm_context_uses_default_system_prompt_when_none(self, tpl):
        fn = tpl.model_context_template("ChatGLMForCausalLM")
        result = fn("question")
        assert LLMPromptTemplate.DEFAULT_SYSTEM_PROMPT_ChatGLM.strip()[:20] in result


# ── individual prompt methods ─────────────────────────────────────────────────

class TestIndividualPromptMethods:
    def test_llama2_default_format(self, tpl):
        result = tpl.llama2_default_prompt("What is 2+2?")
        assert result == "<s>[INST] What is 2+2? [/INST]"

    def test_gemma_default_ends_with_model_turn(self, tpl):
        result = tpl.gemma_default_prompt("What is 2+2?")
        assert result.endswith("<start_of_turn>model\n")

    def test_chatglm_default_contains_assistant_tag(self, tpl):
        result = tpl.chatglm_default_prompt("What is 2+2?")
        assert "<|assistant|>" in result

    def test_llama_context_prompt_wraps_completion(self, tpl):
        result = tpl.llama_context_propmt("Tell me about AI.")
        assert "Tell me about AI." in result
        assert "[INST]" in result

    def test_gemma_context_wraps_completion(self, tpl):
        result = tpl.gemma_context_prompt("Tell me about AI.")
        assert "Tell me about AI." in result

    def test_chatglm_context_default_system(self, tpl):
        result = tpl.chatglm_context_prompt("query text")
        assert "query text" in result

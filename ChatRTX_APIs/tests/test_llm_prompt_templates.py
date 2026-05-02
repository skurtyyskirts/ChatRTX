import pytest
from ChatRTX.llm_prompt_templates import LLMPromptTemplate


@pytest.fixture
def template():
    return LLMPromptTemplate()


class TestModelDefaultTemplate:
    def test_llama2_wraps_query_in_inst_tags(self, template):
        result = template.model_default_template("LlamaForCausalLM", "hello")
        assert result == "<s>[INST] hello [/INST]"

    def test_gemma_wraps_query_in_turn_tags(self, template):
        result = template.model_default_template("GemmaForCausalLM", "hello")
        assert "<start_of_turn>user" in result
        assert "hello" in result
        assert "<start_of_turn>model" in result

    def test_chatglm_wraps_query_with_user_tag(self, template):
        result = template.model_default_template("ChatGLMForCausalLM", "hello")
        assert "<|user|>" in result
        assert "hello" in result
        assert "<|assistant|>" in result

    def test_unknown_model_returns_query_unchanged(self, template):
        result = template.model_default_template("UnknownModel", "test query")
        assert result == "test query"

    def test_query_with_special_characters(self, template):
        query = "What is 2+2? It's <math>."
        result = template.model_default_template("LlamaForCausalLM", query)
        assert query in result

    def test_empty_query(self, template):
        result = template.model_default_template("LlamaForCausalLM", "")
        assert result == "<s>[INST]  [/INST]"


class TestModelContextTemplate:
    def test_llama_returns_callable(self, template):
        fn = template.model_context_template("LlamaForCausalLM")
        assert callable(fn)

    def test_gemma_returns_callable(self, template):
        fn = template.model_context_template("GemmaForCausalLM")
        assert callable(fn)

    def test_chatglm_returns_callable(self, template):
        fn = template.model_context_template("ChatGLMForCausalLM")
        assert callable(fn)

    def test_unknown_model_returns_none(self, template):
        result = template.model_context_template("UnknownModel")
        assert result is None

    def test_llama_context_contains_system_prompt(self, template):
        fn = template.model_context_template("LlamaForCausalLM")
        result = fn("user message")
        assert "[INST]" in result
        assert "user message" in result
        assert "helpful" in result

    def test_gemma_context_contains_completion(self, template):
        fn = template.model_context_template("GemmaForCausalLM")
        result = fn("user message")
        assert "user message" in result
        assert "<start_of_turn>" in result

    def test_chatglm_context_contains_system_and_completion(self, template):
        fn = template.model_context_template("ChatGLMForCausalLM")
        result = fn("user message")
        assert "user message" in result


class TestIndividualPromptMethods:
    def test_llama2_default_prompt_format(self, template):
        result = template.llama2_default_prompt("What is AI?")
        assert result.startswith("<s>[INST]")
        assert result.endswith("[/INST]")
        assert "What is AI?" in result

    def test_gemma_default_prompt_format(self, template):
        result = template.gemma_default_prompt("Tell me a story")
        assert result.startswith("<start_of_turn>user")
        assert "Tell me a story" in result
        assert "<start_of_turn>model" in result

    def test_chatglm_default_prompt_includes_role_tags(self, template):
        result = template.chatglm_default_prompt("你好")
        assert "<|user|>" in result
        assert "你好" in result
        assert "<|assistant|>" in result

    def test_llama_context_prompt_uses_inst_tags(self, template):
        result = template.llama_context_propmt("How does RAG work?")
        assert "How does RAG work?" in result
        assert "[INST]" in result
        assert "[/INST]" in result

    def test_gemma_context_prompt_has_turn_structure(self, template):
        result = template.gemma_context_prompt("Explain TensorRT")
        assert "Explain TensorRT" in result
        assert "<start_of_turn>" in result

    def test_chatglm_context_prompt_default_system(self, template):
        result = template.chatglm_context_prompt("Hello")
        assert "Hello" in result
        assert template.B_SYS_CHATGLM in result

    def test_chatglm_context_prompt_custom_system(self, template):
        result = template.chatglm_context_prompt("Hello", system_prompt="Be concise.")
        assert "Be concise." in result
        assert "Hello" in result

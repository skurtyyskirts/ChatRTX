# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: MIT

import unittest
from ChatRTX.llm_prompt_templates import LLMPromptTemplate

class TestLLMPromptTemplate(unittest.TestCase):
    def setUp(self):
        self.template = LLMPromptTemplate()

    def test_model_context_template_llama(self):
        method = self.template.model_context_template("LlamaForCausalLM")
        self.assertEqual(method, self.template.llama_context_propmt)

    def test_model_context_template_gemma(self):
        method = self.template.model_context_template("GemmaForCausalLM")
        self.assertEqual(method, self.template.gemma_context_prompt)

    def test_model_context_template_chatglm(self):
        method = self.template.model_context_template("ChatGLMForCausalLM")
        self.assertEqual(method, self.template.chatglm_context_prompt)

    def test_model_context_template_unknown(self):
        method = self.template.model_context_template("UnknownModel")
        self.assertIsNone(method)

    def test_llama2_default_prompt(self):
        query = "Hello"
        expected = "<s>[INST] Hello [/INST]"
        self.assertEqual(self.template.llama2_default_prompt(query), expected)

    def test_gemma_default_prompt(self):
        query = "Hello"
        expected = (
            "<start_of_turn>user\n"
            "Hello<end_of_turn>\n"
            "<start_of_turn>model\n")
        self.assertEqual(self.template.gemma_default_prompt(query), expected)

    def test_llama_context_propmt(self):
        completion = "The capital of France is Paris."
        result = self.template.llama_context_propmt(completion)
        self.assertIn("<<SYS>>", result)
        self.assertIn(completion, result)
        self.assertTrue(result.startswith("<s> [INST]"))
        self.assertTrue(result.endswith("[/INST]"))

    def test_gemma_context_prompt(self):
        completion = "The capital of France is Paris."
        result = self.template.gemma_context_prompt(completion)
        self.assertIn("<start_of_turn>user \n", result)
        self.assertIn(completion, result)
        self.assertIn("<end_of_turn><start_of_turn>model ", result)

    def test_chatglm_default_prompt(self):
        query = "Hello"
        result = self.template.chatglm_default_prompt(query)
        self.assertIn("<|system|>\n", result)
        self.assertIn("ChatGLM3", result)
        self.assertIn("<|user|>\nHello\n", result)
        self.assertIn("<|assistant|>", result)

    def test_chatglm_context_prompt_default_system(self):
        completion = "The capital of France is Paris."
        result = self.template.chatglm_context_prompt(completion)
        self.assertIn("<|system|>\n", result)
        self.assertIn(self.template.DEFAULT_SYSTEM_PROMPT_ChatGLM.strip(), result)
        self.assertIn(completion, result)

    def test_chatglm_context_prompt_custom_system(self):
        completion = "The capital of France is Paris."
        system_prompt = "You are a geography expert."
        result = self.template.chatglm_context_prompt(completion, system_prompt=system_prompt)
        self.assertIn("<|system|>\n", result)
        self.assertIn(system_prompt, result)
        self.assertIn(completion, result)

    def test_model_default_template_llama(self):
        query = "Hello"
        result = self.template.model_default_template("LlamaForCausalLM", query)
        self.assertEqual(result, self.template.llama2_default_prompt(query))

    def test_model_default_template_unknown(self):
        query = "Hello"
        result = self.template.model_default_template("UnknownModel", query)
        self.assertEqual(result, query)

if __name__ == "__main__":
    unittest.main()

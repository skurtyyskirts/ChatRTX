# SPDX-FileCopyrightText: Copyright (c) 2023-2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: MIT
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Sequence

import gc
import time
import uuid
import torch
from ChatRTX.inference.trtllm.trtllm import TrtLlm
from llama_index.core.bridge.pydantic import Field, PrivateAttr
from llama_index.core.base.llms.types import (
    ChatMessage,
    ChatResponse,
    CompletionResponse,
    ChatResponseGen,
    CompletionResponseGen,
    LLMMetadata
)
from llama_index.core.base.llms.generic_utils import (
    completion_response_to_chat_response,
    stream_completion_response_to_chat_response,
)
from llama_index.core.callbacks import CallbackManager
from llama_index.core.constants import DEFAULT_CONTEXT_WINDOW, DEFAULT_NUM_OUTPUTS
from llama_index.core.llms.callbacks import llm_chat_callback, llm_completion_callback
from llama_index.core.llms.custom import CustomLLM


@dataclass
class TrtLlmAPIConfig:
    model_path: Optional[str] = None
    tokenizer_dir: Optional[str] = None
    vocab_file: Optional[str] = None
    temperature: float = 0.1
    max_new_tokens: int = DEFAULT_NUM_OUTPUTS
    context_window: int = DEFAULT_CONTEXT_WINDOW
    completion_to_prompt: Optional[Callable] = None
    prompt_template: Optional[Any] = None
    callback_manager: Optional[CallbackManager] = None
    generate_kwargs: Optional[Dict[str, Any]] = None
    model_kwargs: Optional[Dict[str, Any]] = None
    use_py_session: bool = True
    add_special_tokens: bool = False
    trtLlm_debug_mode: bool = False

class TrtLlmAPI(CustomLLM):
    """A custom LLM class for handling models optimized with TensorRT.

    Attributes:
        messages_to_prompt (Callable): Function to convert messages to a prompt.
        completion_to_prompt (Callable): Function to convert model completions to prompts.
        generate_kwargs (Dict[str, Any]): Keyword arguments used for text generation.
        model_kwargs (Dict[str, Any]): Keyword arguments for model initialization.
    """
    messages_to_prompt: Callable = Field(
        description="The function to convert messages to a prompt.", exclude=True
    )
    completion_to_prompt: Callable = Field(
        description="The function to convert a completion to a prompt.", exclude=True
    )
    generate_kwargs: Dict[str, Any] = Field(
        default_factory=dict, description="Kwargs used for generation."
    )
    model_kwargs: Dict[str, Any] = Field(
        default_factory=dict, description="Kwargs used for model initialization."
    )

    _model: Any = PrivateAttr()
    _model_path: Any = PrivateAttr()
    _verbose = PrivateAttr()
    _context_window = PrivateAttr()
    _max_new_tokens = PrivateAttr()

    def __init__(self, config: TrtLlmAPIConfig) -> None:
        """Initialize the LlamaIndexTrtLlm class with specified parameters.

        Args:
            config (TrtLlmAPIConfig): Configuration object containing initialization parameters.
        """
        self._model = TrtLlm(
            model_path=config.model_path,
            tokenizer_dir=config.tokenizer_dir,
            temperature=config.temperature,
            max_new_tokens=config.max_new_tokens,
            context_window=config.context_window,
            vocab_file=config.vocab_file,  # Previously was set as None mistakenly.
            use_py_session=config.use_py_session,
            add_special_tokens=config.add_special_tokens,
            trtLlm_debug_mode=config.trtLlm_debug_mode
        )

        self._model_path = config.model_path
        self._context_window = config.context_window
        self._max_new_tokens = config.max_new_tokens

        model_kwargs = config.model_kwargs or {}
        model_kwargs.update({"n_ctx": config.context_window, "verbose": False})
        generate_kwargs = config.generate_kwargs or {}
        generate_kwargs.update({"temperature": config.temperature, "max_tokens": config.max_new_tokens})

        super().__init__(
            model_path=config.model_path,
            temperature=config.temperature,
            context_window=config.context_window,
            max_new_tokens=config.max_new_tokens,
            messages_to_prompt=None,
            completion_to_prompt=config.completion_to_prompt,
            callback_manager=config.callback_manager,
            generate_kwargs=generate_kwargs,
            model_kwargs=model_kwargs,
            verbose=False,
        )

    def generate_completion_dict(self, text_str):
        """
        Generate a dictionary for text completion details.

        Args:
            text_str (str): The generated text string from the model.

        Returns:
            dict: A dictionary containing completion details including the text,
                  a unique completion ID, and metadata about the generation.
        """
        completion_id: str = f"cmpl-{str(uuid.uuid4())}"
        created: int = int(time.time())
        model_name: str = self._model_name if hasattr(self, '_model_name') else 'Unknown'

        return {
            "id": completion_id,
            "object": "text_completion",
            "created": created,
            "model": model_name,
            "choices": [
                {
                    "text": text_str,
                    "index": 0,
                    "logprobs": None,
                    "finish_reason": 'stop'
                }
            ],
            "usage": {
                "prompt_tokens": None,
                "completion_tokens": None,
                "total_tokens": None
            }
        }

    @classmethod
    def class_name(cls) -> str:
        """Return the class name as a string."""
        return cls.__name__

    @llm_chat_callback()
    def chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse:
        """
        Process a sequence of chat messages and return a chat response.

        Args:
            messages (Sequence[ChatMessage]): A sequence of messages to process.
            kwargs (dict): Additional keyword arguments for processing.

        Returns:
            ChatResponse: The response generated from the processed chat messages.
        """

        prompt = self.messages_to_prompt(messages)
        completion_response = self.complete(prompt, formatted=True, **kwargs)
        return completion_response_to_chat_response(completion_response)

    @llm_chat_callback()
    def stream_chat(
        self, messages: Sequence[ChatMessage], **kwargs: Any
    ) -> ChatResponseGen:

        """
        Process a sequence of chat messages and return a streaming chat response.

        This method streams the chat response as it is generated, allowing for real-time
        interaction and potentially large-scale processing without waiting for the full response.

        Args:
            messages (Sequence[ChatMessage]): A sequence of chat messages to be processed.
            kwargs (dict): Additional keyword arguments that may influence the response.

        Returns:
            ChatResponseGen: A generator that yields chat response parts as they are generated.
        """

        prompt = self.messages_to_prompt(messages)
        completion_response = self.stream_complete(prompt, formatted=True, **kwargs)
        return stream_completion_response_to_chat_response(completion_response)

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        """
        Generate a completion response from a given prompt.

        Args:
            prompt (str): The prompt to process.
            kwargs (dict): Additional keyword arguments for completion generation.

        Returns:
            CompletionResponse: Structured response containing the text and metadata.
        """
        kwargs.pop("formatted", False)
        output_txt = self._model.complete(prompt, **kwargs)
        return CompletionResponse(text=output_txt, raw=self.generate_completion_dict(output_txt))

    @llm_completion_callback()
    def stream_complete(
        self, prompt: str, formatted: bool = False, **kwargs: Any
    ) -> CompletionResponseGen:

        """
        Stream completions for a given prompt in a generator fashion.

        This function is designed to generate and yield completion responses incrementally,
        which is useful for handling long or continuous interactions without needing to wait
        for a full completion.

        Args:
            prompt (str): The prompt to generate completions for.
            formatted (bool): Indicates whether the prompt is pre-formatted.
            kwargs (dict): Additional keyword arguments for dynamic completion generation.

        Returns:
            CompletionResponseGen: A generator that yields completion responses as generated.
        """

        self.generate_kwargs.update({"stream": True})

        if not formatted:
            prompt = self.completion_to_prompt(prompt)

        response_iter = self._model.stream_complete(prompt=prompt, **kwargs)

        def gen() -> CompletionResponseGen:
            text = ""
            for response in response_iter:
                delta = response
                text += delta
                yield CompletionResponse(delta=delta, text=text, raw=self.generate_completion_dict(response))

        return gen()

    def unload_llm(self):
        """
        Unload the model from memory and perform necessary cleanup.
        """
        if self._model is not None:
            del self._model
            self._model = None  # Ensure the reference is cleaned up after deletion.

        torch.cuda.empty_cache()
        gc.collect()

    @property
    def metadata(self) -> LLMMetadata:
        """LLM metadata."""
        return LLMMetadata(
            context_window=self._context_window,
            num_output=self._max_new_tokens,
            model_name=self._model_path,
        )

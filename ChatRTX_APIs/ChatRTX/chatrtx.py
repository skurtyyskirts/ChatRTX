# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

from ChatRTX.inference.trtllm.trtllm import TrtLlm, TrtLlmConfig
from ChatRTX.inference.pytorch.CLIP import ClipInference
from ChatRTX.llm_prompt_templates import LLMPromptTemplate
import os, json
from ChatRTX.logger import ChatRTXLogger, LoggerConfig
import logging

class ChatRTX:
    """
    Manages operations on language models including initialization, and response generation.
    """
    # Class-level constants for directory and file names
    ENGINE_DIR = "engine"
    ENGINE_NAME = "engine"
    MODEL_DIR = "model"
    TOKENIZER_DIR = "tokenizer_local_dir"
    VOCAB_DIR = "vocab_local_dir"
    VOCAB_FILE_KEY = "vocab_file"

    def __init__(self, models_info_map, model_download_dir):
        """
        Initialize the ChatRTX object.

        :param models_info_map: A list of dictionaries containing model information.
        """
        self._models_info_map = models_info_map
        self._model_directory = os.path.join(model_download_dir, "models")
        self._llm = None

        # Initialize the logger
        ChatRTXLogger(LoggerConfig(log_level=logging.INFO, log_file='ChatRTX.log'))
        self._logger = ChatRTXLogger.get_logger()
        app_config = os.path.join(os.path.dirname(os.path.abspath(__file__)), "./config/app_config.json")
        self._app_config_info = self._load_config(app_config)

    def init_llm_model(self, model_id, backend="TRTLLM", **kwqags):
        try:
            model_info = next((info for info in self._models_info_map if info["id"] == model_id), None)
            if model_info is None:
                self._logger.error("Model ID '%s' not found in the configuration.", model_id)
                raise ValueError(f"Model ID '{model_id}' not found in the configuration.")

            if backend != "TRTLLM":
                self._logger.error("Unsupported backend '%s'. Currently, only 'TRTLLM' is supported.", backend)
                raise ValueError(f"Unsupported backend '{backend}'. Currently, only 'TRTLLM' is supported.")

            model_path = os.path.join(self._model_directory, model_info["id"], ChatRTX.ENGINE_DIR)
            engine_file_path = os.path.join(model_path, model_info["metadata"].get(ChatRTX.ENGINE_NAME, ""))
            tokenizer_dir = os.path.join(self._model_directory, model_info["id"],
                                         model_info.get("prerequisite", {}).get(ChatRTX.TOKENIZER_DIR, "")) \
                                                    if ("tokenizer_local_dir" in model_info["prerequisite"]) else None

            vocab_file = os.path.join(self._model_directory, model_info["id"],
                                      model_info["prerequisite"][ChatRTX.VOCAB_DIR],
                                      model_info["prerequisite"]["tokenizer_files"]["vocab_file"]) \
                                                    if (ChatRTX.VOCAB_DIR in model_info["prerequisite"]) else None

            self._logger.debug("Model path: %s", model_path)
            self._logger.debug("Engine file path: %s", engine_file_path)
            self._logger.debug("Tokenizer directory: %s", tokenizer_dir)
            self._logger.debug("Vocab file: %s", vocab_file)

            use_py_session = kwqags['use_py_session'] if 'use_py_session' in kwqags else self._app_config_info['use_py_session']
            add_special_tokens = kwqags['add_special_tokens'] if 'add_special_tokens' in kwqags else self._app_config_info['add_special_tokens']
            trtLlm_debug_mode = kwqags['trtLlm_debug_mode'] if 'trtLlm_debug_mode' in kwqags else self._app_config_info['trtLlm_debug_mode']

            config = TrtLlmConfig(
                model_path=model_path,
                tokenizer_dir=tokenizer_dir,
                temperature=model_info["metadata"].get("temperature", 0.1),
                max_new_tokens=model_info["metadata"].get("max_new_tokens", None),
                context_window=model_info["metadata"].get("max_input_token", None),
                vocab_file=vocab_file,
                use_py_session=use_py_session,
                add_special_tokens=add_special_tokens,
                trtLlm_debug_mode=trtLlm_debug_mode
            )
            self._llm = TrtLlm(config)
            return True
        except Exception as e:
            self._logger.error(f"Failed to init TRTLLM model object: Error {str(e)}")
            return False

    def init_clip_model(self, model_id):
        try:
            model_info = next((info for info in self._models_info_map if info["id"] == model_id), None)
            if model_info is None:
                self._logger.error("Model ID '%s' not found in the configuration.", model_id)
                raise ValueError(f"Model ID '{model_id}' not found in the configuration.")

            model_path = os.path.join(self._model_directory, model_info["id"])

            self.clip_inference = ClipInference()
            status = self.clip_inference.load_model(model_path)
            return status
        except Exception as e:
            self._logger.error(f"Failed to init clip model object: Error {str(e)}")
            return False

    def generate_clip_engine(self, image_data_dir , force_rewrite = True):
        if self.clip_inference is not None:
            return self.clip_inference.generate_clip_engine(image_data_dir , force_rewrite = True)
        else:
            self._logger.error("No clip inferance object")
            return False

    def generate_clip_response(self, input_text, top_matches_path, min_clip_score):
        if self.clip_inference is not None:
            return self.clip_inference.generate_clip_response(input_text, top_matches_path, min_clip_score)
        else:
            self._logger.error("No clip inferance object")
            return False

    def generate_response(self, query):
        if self._llm is None:
            self._logger.error("No model is loaded. Please load a model before generating responses")
            raise Exception("No model is loaded. Please load a model before generating responses.")

        try:
            prompt_template = LLMPromptTemplate()
            prompt = prompt_template.model_default_template(model=self._llm.get_model_name(), query=query)
            return self._llm.complete(prompt)
        except Exception as e:
            self._logger.error(f"Failed to generate the response: Error: {str(e)}")
            raise Exception(f"Failed to generate the response {str(e)}")

    def generate_stream_response(self, query):
        if self._llm is None:
            self._logger.error("No model is loaded. Please load a model before generating responses")
            raise Exception("No model is loaded. Please load a model before generating responses.")

        try:
            prompt_template = LLMPromptTemplate()
            prompt = prompt_template.model_default_template(model=self._llm.get_model_name(), query=query)
            response_tokens = self._llm.stream_complete(prompt)
            for response in response_tokens:
                yield response
                
        except Exception as e:
            self._logger.error(f"Failed to generate the stream response: Error {str(e)}")
            raise Exception(f"Failed to generate the stream response {str(e)}")

    def unload_llm(self):
        if self._llm is not None:
            try:
                self._llm.unload_llm()
                self._llm = None
                self._logger.info("Language model unloaded successfully.")
            except Exception as e:
                self._logger.error(f"Failed to unload the language model: Error {str(e)}")
                raise Exception(f"Failed to unload the language model: {str(e)}")

    def _load_config(self, file_name):
        try:
            with open(file_name, 'r', encoding='utf8') as file:
                return json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"The configuration file {file_name} was not found.")
        except json.JSONDecodeError:
            raise ValueError(f"There was an error decoding the JSON from the file {file_name}.")
        except Exception as e:
            raise Exception(f"An unexpected error occurred: {e}")
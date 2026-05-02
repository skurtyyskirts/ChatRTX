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

import logging
import logging.handlers
import os
from dataclasses import dataclass


@dataclass
class LoggerConfig:
    log_level: int = logging.DEBUG
    log_file: str = None
    log_format: str = None
    max_bytes: int = 10485760
    backup_count: int = 5

class ChatRTXLogger:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ChatRTXLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self, config: LoggerConfig = None):
        config = config or LoggerConfig()
        if hasattr(self, '_initialized') and self._initialized:
            return

        self._initialized = True

        if config.log_format is None:
            config.log_format = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'

        self.logger = logging.getLogger("[ChatRTX]")
        self.logger.setLevel(config.log_level)

        formatter = logging.Formatter(config.log_format)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler
        if config.log_file:

            log_dir = os.path.dirname(config.log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)

            # Check if the file exists, and create it if it does not
            if not os.path.exists(config.log_file):
                open(config.log_file, 'w').close()

            file_handler = logging.handlers.RotatingFileHandler(config.log_file, maxBytes=config.max_bytes, backupCount=config.backup_count)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    @staticmethod
    def get_logger():
        return ChatRTXLogger().logger

    @staticmethod
    def set_log_level(level):
        logger = ChatRTXLogger.get_logger()
        logger.setLevel(level)
        for handler in logger.handlers:
            handler.setLevel(level)

    @staticmethod
    def set_verbose_mode(enable):
        level = logging.DEBUG if enable else logging.INFO
        ChatRTXLogger.set_log_level(level)

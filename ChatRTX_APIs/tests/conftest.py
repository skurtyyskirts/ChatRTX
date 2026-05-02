import sys
import os
from unittest.mock import MagicMock

# Make the ChatRTX_APIs package importable without installation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Stub out heavy optional dependencies that are not available in the CI test env
_UNAVAILABLE = [
    # Third-party packages not installed in the CI test environment
    "ngcsdk",
    "requests",
    "faiss",
    "torch",
    "tqdm",
    "llama_index",
    "llama_index.core",
    "llama_index.embeddings",
    "llama_index.embeddings.huggingface",
    "llama_index.vector_stores",
    "llama_index.vector_stores.faiss",
    "llama_index.core.node_parser",
]
for _mod in _UNAVAILABLE:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

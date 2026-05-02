# ChatRTX — LLM Assistant Bootstrap

NVIDIA ChatRTX: a local AI chatbot running on RTX GPUs using TensorRT-LLM.

## Repo Structure

```
ChatRTX_APIs/         Python APIs — model loading, inference, RAG pipeline
ChatRTX_App/
  app_launch.py       Main application entry point
  app_launch.bat      Windows launcher
  ChatRTXUI/          Web-based front-end
  requirements.txt    Python dependencies
  pyproject.toml      Poetry project config
setup.cfg             Package config
3rd_party_license.txt Third-party license attributions
```

## Entry Point

`ChatRTX_App/app_launch.py` — sets up environment and starts the app and UI server.

## Run

```cmd
cd ChatRTX_App
pip install -r requirements.txt
python app_launch.py
```

Or use `ChatRTX_App/app_launch.bat` on Windows (recommended — sets correct env vars).

## Key APIs (`ChatRTX_APIs/`)

- Model loading and switching (Mistral, LLaMA, Gemma, etc.)
- RAG document ingestion pipeline (PDF, TXT, URL)
- TensorRT-LLM inference wrapper
- Chat session management

## Platform Notes

- Windows-first; targets RTX 30xx/40xx hardware (TensorRT-LLM backend)
- Requires CUDA + TensorRT; no macOS/Linux support in main branch
- Third-party licenses documented in `3rd_party_license.txt`

## Testing

No test suite currently. Integration testing is manual via the UI at `http://localhost:<port>`.

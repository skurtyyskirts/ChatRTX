# ChatRTX — LLM Assistant Bootstrap

NVIDIA ChatRTX: a local AI chatbot running on RTX GPUs using TensorRT-LLM.

## Repo Structure

```
ChatRTX_APIs/         Python APIs — model loading, inference, RAG pipeline
ChatRTX_APIs/tests/   Unit tests for the Python APIs
ChatRTX_App/
  app_launch.py       Main application entry point (requires built UI)
  app_launch.bat      Windows launcher (sets correct env vars)
  ChatRTXUI/          Electron/web front-end
    engine/tests/     UI engine tests
  requirements.txt    Python dependencies
  pyproject.toml      Poetry project config
setup.cfg             Package config (includes flake8 config)
3rd_party_license.txt Third-party license attributions
```

## Entry Point

`ChatRTX_App/app_launch.py` — sets up environment and launches the packaged
Electron UI. Requires the UI to be built first (see Run below).

## Run

The Electron UI must be built before `app_launch.py` will work:

```cmd
cd ChatRTX_App\ChatRTXUI
npm install
npm run build-electron
cd ..
python app_launch.py
```

For day-to-day development on Windows, use the batch launcher which sets
all required env vars:
```cmd
cd ChatRTX_App
app_launch.bat
```

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

```bash
# API unit tests:
pytest ChatRTX_APIs/tests/ -v

# UI engine tests:
pytest ChatRTX_App/ChatRTXUI/engine/tests/ -v
```

End-to-end testing of the full UI is manual via the browser at `http://localhost:<port>`.

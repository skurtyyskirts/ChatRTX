# ChatRTX — Automated Self-Healing CI/CD Setup Guide

**Date:** 2026-05-02  
**Repo:** `skurtyyskirts/ChatRTX`

This document walks through every manual step required to activate the
fully automated test → fix → merge loop. Once complete, no human
intervention is needed for the loop to run.

---

## How the Loop Works

```
Push / PR
    │
    ▼
GitHub Actions: pytest
    │
    ├─ PASS ──► (on PR) Auto-merge into main ✓
    │
    └─ FAIL ──► AI Fixer reads logs
                    │
                    ▼
               Claude (claude-sonnet-4-6) proposes patch
                    │
                    ▼
               Patch committed → pushed to same branch
                    │
                    ▼
               pytest runs again  (loop repeats, max 5× per push)
```

---

## Step 1 — Create a GitHub Personal Access Token (PAT)

1. Go to **GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens**.
2. Click **Generate new token**.
3. Set **Repository access** to `skurtyyskirts/ChatRTX`.
4. Grant these permissions:
   - **Contents** → Read & write
   - **Pull requests** → Read & write
   - **Workflows** → Read & write
5. Copy the token — you won't see it again.

---

## Step 2 — Add Repository Secrets

Go to **GitHub → skurtyyskirts/ChatRTX → Settings → Secrets and variables → Actions**.

Add these two secrets:

| Secret name         | Value                                      |
|---------------------|--------------------------------------------|
| `GH_PAT`            | The PAT you just created                   |
| `ANTHROPIC_API_KEY` | Your Anthropic API key (from console.anthropic.com) |

---

## Step 3 — Enable Auto-Merge on the Repository

1. Go to **Settings → General → Pull Requests**.
2. Check ✅ **Allow auto-merge**.
3. Check ✅ **Automatically delete head branches** (optional but recommended).

---

## Step 4 — Add a Branch Protection Rule for `main`

1. Go to **Settings → Branches → Add rule**.
2. Branch name pattern: `main`
3. Enable these options:
   - ✅ **Require a pull request before merging**
   - ✅ **Require status checks to pass before merging**
     - Search for and add the status check named **`pytest`**
   - ✅ **Require branches to be up to date before merging**
   - ✅ **Do not allow bypassing the above settings**
4. Click **Save changes**.

> **Why?** This ensures `main` only ever receives code that has passed tests.
> The `auto_merge` job in CI calls `gh pr merge --auto`, which GitHub will
> execute as soon as the `pytest` check turns green.

---

## Step 5 — Verify the Workflow File Is Committed

The file `.github/workflows/ci.yml` must exist on your branch. If you
just cloned the repo and haven't pushed yet:

```powershell
cd C:\Users\skurtyy\Documents\GitHub\ChatRTX
git add .
git commit -m "feat: add automated CI/CD and self-healing test loop"
git push origin main
```

---

## Step 6 — Working Branch Strategy

The AI fixer only runs on **non-main** branches. Your workflow is:

```
1. Create a feature branch
   git checkout -b feature/my-change

2. Make changes, push
   git push origin feature/my-change

3. Open a Pull Request to main

4. If tests fail → AI fixer auto-commits a fix to your branch
   → tests re-run → if green, PR auto-merges into main
```

---

## File Reference

| File | Purpose |
|------|---------|
| `.github/workflows/ci.yml` | Orchestrates test, AI-fix, and auto-merge jobs |
| `scripts/ai_fixer.py` | Reads pytest logs, calls Claude, applies patch, pushes commit |
| `tests/test_prompt_templates.py` | Tests for `LLMPromptTemplate` (pure Python) |
| `tests/test_logger.py` | Tests for `ChatRTXLogger` (pure Python) |
| `tests/test_config.py` | Tests for `Config` class (pure Python) |
| `tests/test_chatrtx_unit.py` | Unit tests for `ChatRTX` with mocked GPU deps |

---

## Running Tests Locally

```powershell
cd C:\Users\skurtyy\Documents\GitHub\ChatRTX
pip install pytest
pytest tests/ -v
```

---

## Dry-Running the AI Fixer Locally

```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
python scripts/ai_fixer.py --logs reports/pytest_output.txt --dry-run
```

This prints the proposed patch without modifying any files or making commits.

---

## Safety Limits

- The AI fixer is capped at one commit per CI run. If the new commit
  also fails, CI triggers again — up to GitHub's concurrency limits.
  The fixer itself won't loop more than `MAX_RETRIES = 5` times per
  manual invocation (relevant for local use).
- The fixer **never touches** the `main` branch directly.
- If Claude returns an empty `changes` list, the fixer exits without
  committing anything — no infinite loops.

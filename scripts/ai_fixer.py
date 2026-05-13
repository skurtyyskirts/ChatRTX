#!/usr/bin/env python3
"""
scripts/ai_fixer.py
───────────────────
Reads a pytest failure log, asks Claude to propose a fix, applies the patch
to the repo, and pushes a new commit back to the current branch.

Environment variables required:
  ANTHROPIC_API_KEY   – Anthropic API key
  GITHUB_TOKEN        – PAT with repo write access  (or GH_PAT)
  GITHUB_REPOSITORY   – e.g. "skurtyyskirts/ChatRTX"
  BRANCH_NAME         – branch that just failed CI

Usage:
  python scripts/ai_fixer.py --logs reports/pytest_output.txt
"""

import argparse
import json
import os
import subprocess
import sys
import textwrap

# ── third-party (installed in the CI step) ────────────────────────────────────
try:
    import anthropic
except ImportError:
    sys.exit("anthropic package not found – run: pip install anthropic")

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

ANTHROPIC_API_KEY  = os.environ.get("ANTHROPIC_API_KEY", "")
GITHUB_TOKEN       = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_PAT", "")
GITHUB_REPOSITORY  = os.environ.get("GITHUB_REPOSITORY", "")
BRANCH_NAME        = os.environ.get("BRANCH_NAME", "")

MAX_RETRIES        = 5    # Safety cap – stop after this many AI-fix iterations per run
MAX_LOG_CHARS      = 8000 # Truncate very long logs before sending to the API
MODEL              = "claude-sonnet-4-6"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def read_log(path: str) -> str:
    """Return the content of the test-failure log (truncated if huge)."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        if len(content) > MAX_LOG_CHARS:
            content = content[-MAX_LOG_CHARS:]  # Keep the tail – most relevant
        return content
    except FileNotFoundError:
        sys.exit(f"[ai_fixer] Log file not found: {path}")


def collect_source_files(root: str = ".") -> dict[str, str]:
    """
    Return a dict of {relative_path: content} for every .py file in the repo
    (excluding .git, __pycache__, venv, etc.).
    """
    skip_dirs = {".git", "__pycache__", "venv", ".venv", "node_modules", "build", "dist"}
    files = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for fname in filenames:
            if not fname.endswith(".py"):
                continue
            full = os.path.join(dirpath, fname)
            rel  = os.path.relpath(full, root)
            try:
                with open(full, "r", encoding="utf-8", errors="replace") as f:
                    files[rel] = f.read()
            except Exception:
                pass
    return files


def ask_claude(failure_log: str, source_files: dict[str, str]) -> dict:
    """
    Ask Claude to diagnose the failures and return a JSON patch plan.

    Returns a dict like:
      {
        "explanation": "...",
        "changes": [
          {"file": "ChatRTX_APIs/ChatRTX/foo.py",
           "old": "def broken():\n    ...",
           "new": "def broken():\n    return True"}
        ]
      }
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    source_summary = "\n\n".join(
        f"### {path}\n```python\n{content[:3000]}\n```"
        for path, content in list(source_files.items())[:20]  # Keep prompt manageable
    )

    system = textwrap.dedent("""
        You are an expert Python engineer working on the ChatRTX project.
        Your job is to fix failing pytest tests by modifying source files
        (NOT the test files themselves unless the tests are wrong).

        You MUST respond with valid JSON only – no markdown fences, no prose.
        The JSON schema is:
        {
          "explanation": "<brief description of the root cause and your fix>",
          "changes": [
            {
              "file": "<relative path from repo root>",
              "old": "<exact string to find and replace>",
              "new": "<replacement string>"
            }
          ]
        }

        Rules:
        - "old" must match the current file content exactly (including whitespace).
        - Make the minimal change required to fix the failures.
        - If you cannot determine a safe fix, return {"explanation": "...", "changes": []}.
        - Do NOT modify test files unless the test itself contains a clear mistake.
    """).strip()

    user = textwrap.dedent(f"""
        ## Failing pytest output
        ```
        {failure_log}
        ```

        ## Source files
        {source_summary}

        Please produce the JSON patch to fix the failures.
    """).strip()

    message = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user}]
    )

    raw = message.content[0].text.strip()

    # Strip accidental markdown fences
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:])
    if raw.endswith("```"):
        raw = "\n".join(raw.split("\n")[:-1])

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[ai_fixer] Claude returned non-JSON: {e}\nRaw:\n{raw[:500]}")
        return {"explanation": "JSON parse error", "changes": []}


def apply_changes(changes: list[dict]) -> list[str]:
    """Apply text-level patches to source files. Returns list of modified paths."""
    modified = []
    for change in changes:
        path = change.get("file", "")
        old  = change.get("old",  "")
        new  = change.get("new",  "")
        if not path or not old:
            print(f"[ai_fixer] Skipping incomplete change entry: {change}")
            continue
        if not os.path.exists(path):
            print(f"[ai_fixer] File not found, skipping: {path}")
            continue
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if old not in content:
            print(f"[ai_fixer] Pattern not found in {path}, skipping.")
            continue
        content = content.replace(old, new, 1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[ai_fixer] Patched: {path}")
        modified.append(path)
    return modified


def git_commit_and_push(modified_files: list[str], message: str):
    """Stage, commit, and push the patched files."""
    subprocess.run(["git", "config", "user.email", "ai-fixer@github-actions"], check=True)
    subprocess.run(["git", "config", "user.name",  "AI Fixer Bot"],            check=True)
    for f in modified_files:
        subprocess.run(["git", "add", f], check=True)
    result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if result.returncode == 0:
        print("[ai_fixer] No staged changes – nothing to commit.")
        return
    subprocess.run(["git", "commit", "-m", message], check=True)
    subprocess.run(["git", "push", "origin", f"HEAD:{BRANCH_NAME}"], check=True)
    print(f"[ai_fixer] Pushed fix commit to {BRANCH_NAME}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI-powered test failure fixer")
    parser.add_argument("--logs", required=True, help="Path to pytest output log")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the proposed patch without applying it")
    args = parser.parse_args()

    # Validate environment
    missing = [v for v in ("ANTHROPIC_API_KEY", "GITHUB_TOKEN", "BRANCH_NAME")
               if not os.environ.get(v)]
    if missing and not args.dry_run:
        sys.exit(f"[ai_fixer] Missing environment variables: {', '.join(missing)}")

    failure_log  = read_log(args.logs)
    source_files = collect_source_files(".")

    print(f"[ai_fixer] Sending {len(failure_log)} chars of log + "
          f"{len(source_files)} source files to Claude {MODEL}…")

    patch = ask_claude(failure_log, source_files)

    print(f"[ai_fixer] Explanation: {patch.get('explanation', '(none)')}")
    changes = patch.get("changes", [])
    print(f"[ai_fixer] Proposed {len(changes)} change(s).")

    if not changes:
        print("[ai_fixer] No changes proposed. Exiting without commit.")
        sys.exit(0)

    if args.dry_run:
        print("[ai_fixer] DRY RUN – patch not applied:")
        print(json.dumps(changes, indent=2))
        sys.exit(0)

    modified = apply_changes(changes)

    if not modified:
        print("[ai_fixer] No files were successfully patched.")
        sys.exit(0)

    commit_msg = (
        f"fix: AI auto-fix [{MODEL}]\n\n"
        f"{patch.get('explanation', '')}\n\n"
        f"Files changed: {', '.join(modified)}"
    )
    git_commit_and_push(modified, commit_msg)


if __name__ == "__main__":
    main()

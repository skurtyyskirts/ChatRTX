# Agent Fleet Index (ChatRTX)

This repo had no `.claude/` directory; this PR bootstraps one.

## Agents added

| Agent | Purpose | Model |
|-------|---------|-------|
| `agent-router` | Recommends which subagent fits a task | haiku |
| `pr-auto-merge-reviewer` | Decides if a PR is safe to auto-merge | sonnet |
| `dependency-auditor` | Vets TensorRT-LLM / torch / cuda / llama-index bumps carefully | sonnet |
| `repo-housekeeper` | Weekly hygiene punch-list | sonnet |
| `feature-prioritizer` | Ranks open ideas/issues | sonnet |
| `rag-evaluator` | Scores RAG pipeline answer quality | sonnet |
| `torch-cuda-debugger` | Diagnoses CUDA/torch/tensorrt runtime errors | sonnet |

## Workflows added

| Workflow | Trigger | Effect |
|----------|---------|--------|
| `auto-merge-on-green.yml` | PR labelled `automerge` | Native squash auto-merge |
| `dependabot-auto-approve.yml` | Dependabot PR (`pull_request_target`) | Auto-approve & label patch/minor |
| `scheduled-housekeeping.yml` | Cron Mon 04:17 UTC | Housekeeping issue |
| `agent-fleet-validator.yml` | PR on `.claude/agents/**` | Lints frontmatter |

## Enabling auto-merge (one-time)

1. Settings → General → **Allow auto-merge** ✓
2. `gh label create automerge -c "#0e8a16"`; `gh label create housekeeping -c "#fbca04"`
3. Apply `automerge` to any PR and let CI go green.

## Terminal recipe for adding more subagents

```bash
claude              # start interactive session in this repo
> /agents           # opens the subagent manager
> Create new agent
```

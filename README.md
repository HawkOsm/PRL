# PRL

A local-first frontend for Claude Code. You talk to a small Ollama model running on your
own GPU; it routes, clarifies, and compiles your requests — and only clean, well-structured
prompts ever reach Claude. Fewer wasted turns, fewer wasted tokens, same subscription.

**Status: early build (M3 done).** The ledger, event models, stats and a golden-case
harness exist and are tested; the local-model parts do not exist yet.

Router scores on the 46 golden cases (`make goldens`):

| router | correct | `must_pass` (21 follow-ups) |
|---|---|---|
| always `TASK_NEW` (baseline) | 12/46 (26.1%) | 0/21 ✗ |
| always `PASSTHROUGH` (baseline) | 24/46 (52.2%) | 21/21 ✓ |
| heuristic rules (no LLM) | 24/46 (52.2%) | 21/21 ✓ |

The rules-only router can only protect follow-ups; telling a new task or a question
apart needs the local model (M4, next). Target: at least 90% with every `must_pass`
case right.

## How it works

```
you ⇄ local 7–8B model (free)        route / clarify / compile
        ▼
   compiled task spec (you approve)
        ▼
   Claude Code session (headless, via claude-agent-sdk)
```

- Trivial questions are answered locally and never cost a Claude token.
- Vague requests get up to 3 clarifying questions — locally, for free — before Claude
  sees anything.
- Short mid-session follow-ups ("yes", "fix the test") pass straight through untouched.
- If the local layer is down, the tool degrades to a plain Claude Code wrapper. Your
  work is never blocked.
- Claude session history is never rewritten — prompt caching stays intact by design.

## Why not just compress prompts?

Anthropic's prompt caching is prefix-based and byte-exact: tools that rewrite conversation
history bust the cache and can make token usage *worse*. The expensive thing isn't prompt
length — it's wasted turns. This project attacks turns.

The metric that will be published here: **tokens and turns per completed task**,
before/after, on real work. No reel-math.

## Docs

- [`docs/design.md`](docs/design.md) — engineering design: requirements, architecture,
  routing policy, schemas, degradation matrix, test strategy.
- [`docs/roadmap.md`](docs/roadmap.md) — phases and milestones.

## Planned stack

Python 3.12 (uv), `claude-agent-sdk`, Ollama (qwen2.5:7b class on an 8GB GPU),
prompt_toolkit, pydantic, pytest.

## License

MIT — see [LICENSE](LICENSE).

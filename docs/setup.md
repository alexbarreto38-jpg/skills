# Agent setup record

This file records how the [Vibe Coding Toolkit](https://github.com/soumatheusgomes/vibe-coding-toolkit)
was adopted in this repository, which parts were applied, and how to repeat the setup.
`AGENTS.md` stays the canonical contributor guide; this file only records the setup itself.

## Revision and date

- Toolkit revision: `f13bb354363dafef8ce8d8f605856cc9e1cc52cc` (2026-10-15), `main`
- Applied: 2026-10-17, through `docs/prompts/12-existing-project-setup.md`
- Environment: an ephemeral cloud Claude Code session. Anything installed on the machine
  would have been lost with the container, so only repository files were changed.

## Baseline before the setup

| Command | Result |
|---|---|
| `make self-test` | pass |
| `make validate` | pass, 0 errors, 7 warnings (`testing-handbook-skills` SKILL.md files over 500 lines) |
| `make check` (full) | not run: `shellcheck`, `shfmt` and `bats` were not installed in the container |

The same commands gave the same results after the setup.

## Decisions

This repository is a plugin and skill marketplace written in Markdown, Python and shell.
It has no application, UI or database, and its harness (`AGENTS.md`, `make check`, the
validator self-test, the CI loadability checks) was already more complete than the
toolkit's template. The adoption therefore reconciles instead of replacing anything:

- **No competing docs.** The toolkit's manifest asks for `PRODUCT.md`, `docs/architecture.md`,
  `docs/design.md`, `docs/onboarding.md` and `docs/quality.md`. Their content already lives
  in `README.md` (catalog and scope) and `AGENTS.md` (structure, onboarding, quality gates).
  A second copy would drift, so the mapping below is recorded instead.
- **`AGENTS.md` keeps its rules.** Where the toolkit template disagrees, the existing rules
  win: no verification scaffolding in prompts, no subagents to double-check your own
  work, no Codex sidecars. Only two bullets were added under "Working effectively in this
  repo": continuity on blockers and handoffs, and suggesting 3–8 review cycles after a change.
- **No project-wide plugin activation.** Enabling Superpowers, Ponytail, Caveman or Context7
  through a committed `.claude/settings.json` would change every contributor's sessions,
  so the maintainer declined it. Install them per user instead (see below).

## Document mapping

| Toolkit target | Canonical location here |
|---|---|
| `README.md` | `README.md` (plugin catalog) |
| `PRODUCT.md` | `README.md` intro and per-plugin `README.md` files |
| `AGENTS.md` | `AGENTS.md` |
| `CLAUDE.md` | `CLAUDE.md` (imports `AGENTS.md`) |
| `docs/architecture.md` | `AGENTS.md` → Technical Reference, Plugin Structure |
| `docs/design.md` | not applicable: no UI |
| `docs/onboarding.md` | `AGENTS.md` → Resources, reference skills |
| `docs/quality.md` | `AGENTS.md` → Quality Standards, Before committing |
| `docs/setup.md` | this file |

## Coverage matrix

| Component | Status | Reason / how to resume |
|---|---|---|
| Shared instructions (`AGENTS.md`/`CLAUDE.md`) | applied | reconciled, see Decisions |
| Setup record (`docs/setup.md`) | applied | this file |
| Superpowers, Ponytail, Caveman | not installed, user's choice | per user: `/plugin marketplace add …` then `/plugin install …`, as in the toolkit's `docs/01-installation.md` |
| Context7 | not installed, user's choice | per user, via its plugin or the remote MCP `https://mcp.context7.com/mcp` |
| RTK | blocked | machine CLI; install locally (`brew install rtk-ai/tap/rtk`, then `rtk init --global`) |
| Graphify | blocked | machine CLI (`uv tool install graphifyy`); low value for a Markdown-heavy repo |
| Claude memory | reused | `CLAUDE.md` → `AGENTS.md` is the memory index |
| Subagent policy | reused | `AGENTS.md` → "Subagents" bullet already covers it |
| Hooks | reused | plugin hooks follow `AGENTS.md` → Hooks; no repo-level hook added |
| Anthropic skills (skill-creator) | reused | available from the client; `AGENTS.md` links the authoring docs |
| ESLint/Biome quality gates | not applicable | no JS/TS application; lint is ruff, shellcheck and shfmt |
| Next.js, Drizzle, Zod, Pino templates | not applicable | no application |
| Vercel skills, agent-browser, Chrome DevTools MCP | not applicable | no web UI |
| Obsidian memory | not applicable | no concrete need |

## Repeating the setup

Open the agent at the repository root and paste:

```text
Leia https://raw.githubusercontent.com/soumatheusgomes/vibe-coding-toolkit/main/docs/prompts/12-existing-project-setup.md e execute integralmente o bloco da seção “Prompt” neste projeto, começando pelo brainstorming.
```

Before applying anything, compare the toolkit's current revision with the one above, keep
the decisions in this file unless the reason for them changed, and update this record.
Then run `make check`.

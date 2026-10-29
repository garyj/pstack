# Why this fork exists

`garyj/pstack` is [`backnotprop/pstack`](https://github.com/backnotprop/pstack) plus the files [APM](https://github.com/microsoft/apm) needs to install pstack into Claude Code and Codex. MarketBuddyAU/pdj depends on this fork in its `apm.yml` (since MarketBuddyAU/pdj#636).

## The problem it works around

From pstack 0.15.20, the mirror ships Cursor's root `plugin.json` with the Agent Plugins `$schema`. APM classifies that package as an `agent_plugin` and deploys no files to the `claude` and `codex` targets. `apm update` then deletes the skill and agent files it deployed before, and still exits 0. A dependency on the `skills/` subdirectory does not work either.

## What the fork adds

- `apm.yml`, with the version copied from `plugin.json`.
- `.apm/skills`, a symlink to `skills/`.
- `.apm/agents`, a real copy of `agents/`. A symlink fails `apm audit` in CI, because the audit runs without `apm_modules/`, skips the symlink and reports both agents as orphaned.

## How it stays in sync

`.github/workflows/sync.yml` runs daily:

1. It merges `backnotprop/pstack` `main`, updates the `apm.yml` version, regenerates `.apm/agents` and pushes to `main`. A merge conflict fails the run, and GitHub emails the owner.
2. It fails if `.apm/agents` differs from `agents/`, or if pstack starts to ship a component that `.apm/` does not cover.
3. When new Cursor commits arrive, the `digest` job summarises the cursor/plugins PRs in that range and opens an issue here. To summarise any range, dispatch the workflow with `from` and `to` Cursor commit SHAs.

GitHub disables scheduled workflows after 60 days with no repo activity. If the fork stops moving, check the Actions tab.

## When to retire it

microsoft/apm#2802, the APM feature that would make the fork unnecessary, was closed as not planned on 2026-10-20. Archive the fork and point pdj back at `backnotprop/pstack` only if `backnotprop/pstack` adds its own `apm.yml`.

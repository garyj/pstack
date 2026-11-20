# How this fork works

This repo lets APM install [pstack](https://github.com/cursor/plugins/tree/main/pstack) into a project:

```bash
apm install garyj/pstack
```

Each night it copies Cursor's generated Claude Code tree of pstack, [`cursor/plugins/harness/pstack/claude-code`](https://github.com/cursor/plugins/tree/main/harness/pstack/claude-code), onto `main`.

## Why the fork exists

APM installs an Agent Plugins package such as Cursor's tree only for the `copilot` target. APM declined to change that in [microsoft/apm#2802](https://github.com/microsoft/apm/issues/2802). This fork adds the files APM needs:

- `apm.yml` names the package and carries pstack's version.
- `.apm/skills` links to `skills/`.
- `.apm/agents` is a copy of `agents/`. With a link, `apm audit` on a clean checkout skips the agents and reports them as orphaned.

## What the sync changes in Cursor's files

Cursor builds the tree to install as a Claude Code plugin. APM installs plain skills and agents instead, and it deploys only `skills/` and `agents/`. It also rewrites every relative link that leaves a skill's folder to a path under the gitignored `apm_modules/`, so a fresh clone or a cloud agent loses the link target. `.github/scripts/adapt.py` makes these changes after each copy:

- It copies the Claude Code adapter, `docs/harness/claude-code.md`, into the `pstack-harness` skill, so APM deploys it. It removes the `pstack:` prefix from skill and agent names, because plain skills and agents have no prefix.
- It points each skill's "read the Claude Code adapter" line at the `pstack-harness` skill.
- It turns every other link that leaves a skill's folder into a `https://github.com/cursor/plugins/blob/main/pstack/...` URL. The adapter tells Claude to read the local copy of such a file when one exists.

`sync.sh` also builds `README.md` from `.github/README-fork.md` followed by Lauren's README.

Do not edit Cursor's files on `main`. The next sync overwrites them. Change `adapt.py` or `.github/README-fork.md` instead.

## The nightly workflow

`.github/workflows/sync.yml` runs at 03:17 UTC:

1. It fails before it copies anything if Cursor's tree gains a new kind of plugin component, such as hooks or MCP servers. `.apm/` covers only skills and agents.
2. It runs `.github/scripts/sync.sh`, writes the newest Cursor commit that changed pstack to `.github/cursor-commit`, and pushes to `main`.
3. If that commit moved, it summarises the merged pstack PRs since the old commit and opens an issue assigned to the repo owner. The issue starts with a TL;DR.
4. If any step fails, it opens an issue titled "pstack sync failed", assigned to the repo owner, or comments on the open one.

To summarise a range again without syncing, run the workflow by hand with the `from` and `to` Cursor commits.

## Run the sync by hand

```bash
git clone --filter=blob:none --no-checkout https://github.com/cursor/plugins.git /tmp/cursor-plugins
git -C /tmp/cursor-plugins sparse-checkout set harness/pstack
git -C /tmp/cursor-plugins checkout main
.github/scripts/sync.sh /tmp/cursor-plugins
```

## When to retire the fork

Retire it when APM installs an Agent Plugins package for the `claude` target, or when every place that needs pstack can install Cursor's plugin directly. Claude Code on the web does not load plugins that a repository's `.claude/settings.json` turns on.

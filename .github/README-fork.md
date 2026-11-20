# garyj/pstack: Lauren's pstack for APM

This repo is [Lauren Tan's pstack](https://github.com/cursor/plugins/tree/main/pstack), copied from Cursor each night and packaged so APM can install it. Lauren's README starts below the line.

Install it in a project:

```bash
apm install garyj/pstack
```

Each night at 03:17 UTC, [`.github/workflows/sync.yml`](.github/workflows/sync.yml) does this:

- It clones `cursor/plugins` and takes `harness/pstack/claude-code`, Cursor's Claude Code build of pstack.
- It stops with an error if that build gains something APM can't install from here, such as hooks or MCP servers.
- It copies `skills/`, `agents/`, `docs/`, `LICENSE`, and `plugin.json` over this repo.
- It runs [`.github/scripts/adapt.py`](.github/scripts/adapt.py), so the skills work when APM installs them:
  - The Claude Code adapter becomes the `pstack-harness` skill.
  - The `pstack:` prefix comes off skill and agent names.
  - Links that leave a skill's folder become `cursor/plugins` URLs.
- It sets the version in `apm.yml`, copies `agents/` to `.apm/agents/`, and saves the Cursor commit in `.github/cursor-commit`.
- It builds this README from this section and Lauren's README, then pushes to `main`.
- If pstack changed, it summarises Lauren's merged PRs and opens an issue assigned to garyj, with a TL;DR first.
- If any step fails, it opens or updates a "pstack sync failed" issue assigned to garyj.

Don't edit Lauren's files here, because the next sync overwrites them. Edit this section in [`.github/README-fork.md`](.github/README-fork.md). [`FORK.md`](FORK.md) explains why the fork exists.

---


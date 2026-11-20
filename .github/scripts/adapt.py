# /// script
# requires-python = ">=3.12"
# ///
"""Adapt Cursor's Claude Code tree of pstack to APM, which installs plain skills and agents, not a plugin.

APM deploys only skills/ and agents/, and it rewrites any relative link that leaves a skill's folder to a path
under the gitignored apm_modules/, so a fresh clone loses the target. This script:

- copies the Claude Code adapter into its own skill, skills/pstack-harness/, so APM deploys it, and drops the
  plugin's `pstack:` name prefix, which plain skills and agents don't have;
- points every link to the adapter at that skill in plain text;
- turns every other link that leaves its skill's folder, or the agents folder, into a cursor/plugins URL.
  The adapter tells Claude to read the local copy of such a URL when one exists.
"""

import re
import sys
from pathlib import Path

BLOB = 'https://github.com/cursor/plugins/blob/main/pstack/'
LINK = re.compile(r'\[([^\]]*)\]\(([^)\s#?]+)([#?][^)\s]*)?\)')
PREFIX = re.compile(r'pstack:(?=[a-z<])')
HARNESS = 'pstack-harness'
FRONTMATTER = f"""---
name: {HARNESS}
description: Maps the Cursor names in pstack skills to Claude Code. Read it once per session before you follow any pstack skill.
disable-model-invocation: true
---

"""

root = Path(sys.argv[1]).resolve()
adapter = root / 'docs/harness/claude-code.md'


def folder(path: Path) -> Path:
    parts = path.relative_to(root).parts
    return root / parts[0] / parts[1] if parts[0] == 'skills' else root / parts[0]


def rewrite(path: Path, text: str) -> str:
    def link(match: re.Match) -> str:
        label, target, suffix = match.group(1), match.group(2), match.group(3) or ''
        if ':' in target or target.startswith('/'):
            return match.group(0)
        resolved = (path.parent / target).resolve()
        if resolved == adapter:
            return f'{label} (the `{HARNESS}` skill)'
        inside = path != adapter and resolved.is_relative_to(folder(path))
        if inside or not resolved.exists():
            return match.group(0)
        return f'[{label}]({BLOB}{resolved.relative_to(root).as_posix()}{suffix})'

    return LINK.sub(link, text)


text, prefixes = PREFIX.subn('', adapter.read_text())
if not prefixes:
    sys.exit(f'{adapter} has no `pstack:` names to drop. Check how it names skills and agents now.')
harness = root / 'skills' / HARNESS / 'SKILL.md'
harness.parent.mkdir(exist_ok=True)
harness.write_text(FRONTMATTER + rewrite(adapter, text))

for path in [*root.glob('skills/**/*.md'), *root.glob('agents/*.md')]:
    if path != harness:
        path.write_text(rewrite(path, path.read_text()))

stale = [
    p.relative_to(root).as_posix() for p in root.glob('skills/**/*.md') if 'harness/claude-code.md' in p.read_text()
]
if stale:
    sys.exit(f'These files still name the adapter by path: {", ".join(stale)}')

# /// script
# requires-python = ">=3.12"
# ///
"""Copy skills/ to .apm/skills/, turning links that leave a skill's folder into GitHub links."""

import re
import shutil
from pathlib import Path

BLOB = 'https://github.com/garyj/pstack/blob/main/'
LINK = re.compile(r'\]\(([^)\s#?]+)([#?][^)\s]*)?\)')

root = Path(__file__).resolve().parents[2]
src = root / 'skills'
dest = root / '.apm' / 'skills'

if dest.is_symlink():
    dest.unlink()
shutil.rmtree(dest, ignore_errors=True)
shutil.copytree(src, dest)

for copy in dest.rglob('*.md'):
    original = src / copy.relative_to(dest)
    skill = src / copy.relative_to(dest).parts[0]

    def rewrite(match):
        target, suffix = match.group(1), match.group(2) or ''
        if ':' in target or target.startswith('/'):
            return match.group(0)
        resolved = (original.parent / target).resolve()
        if resolved.is_relative_to(skill) or not resolved.is_relative_to(root) or not resolved.exists():
            return match.group(0)
        return f']({BLOB}{resolved.relative_to(root).as_posix()}{suffix})'

    text = copy.read_text()
    new = LINK.sub(rewrite, text)
    if new != text:
        copy.write_text(new)

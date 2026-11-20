# /// script
# requires-python = ">=3.12"
# dependencies = ["anthropic>=1.15"]
# ///
"""Summarise the cursor/plugins PRs that changed pstack between two commits.

Usage: digest.py <old commit> <new commit> <cursor/plugins clone> <output dir>
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import anthropic

REPO = 'cursor/plugins'
MODEL = 'claude-sonnet-5-5'
PROMPT = Path(__file__).with_name('digest-prompt.md').read_text()
PR_NUMBER = re.compile(r'\(#(\d+)\)$')


def gh(path: str) -> list | dict:
    out = subprocess.run(['gh', 'api', '--paginate', '--slurp', path], capture_output=True, text=True, check=True)
    pages = json.loads(out.stdout)
    return [item for page in pages for item in page] if isinstance(pages[0], list) else pages[0]


def git(clone: Path, *args: str) -> str:
    return subprocess.run(['git', '-C', str(clone), *args], capture_output=True, text=True, check=True).stdout


def version(clone: Path, sha: str) -> str:
    return json.loads(git(clone, 'show', f'{sha}:pstack/.cursor-plugin/plugin.json'))['version']


def pull_requests(clone: Path, old: str, new: str) -> list[dict]:
    prs = {}
    for line in git(clone, 'log', '--reverse', '--format=%H %s', f'{old}..{new}', '--', 'pstack').splitlines():
        sha, subject = line.split(' ', 1)
        found = [pr for pr in gh(f'repos/{REPO}/commits/{sha}/pulls') if pr['merged_at']]
        # A commit pushed by rebase or by hand has no linked PR, but its subject still names one.
        if not found and (number := PR_NUMBER.search(subject)):
            pr = gh(f'repos/{REPO}/pulls/{number[1]}')
            found = [pr] if pr['merged_at'] else []
        for pr in found:
            if not pr['title'].startswith('chore(pstack): bump'):
                prs[pr['number']] = pr
    return [
        {
            'number': pr['number'],
            'url': pr['html_url'],
            'title': pr['title'],
            'author': pr['user']['login'],
            'description': clean(pr['body']),
            'files': [
                f"{f['filename']} (+{f['additions']} -{f['deletions']})"
                for f in gh(f"repos/{REPO}/pulls/{pr['number']}/files?per_page=100")
                if f['filename'].startswith('pstack/')
            ],
        }
        for pr in sorted(prs.values(), key=lambda pr: pr['merged_at'])
    ]


def clean(body: str | None) -> str:
    body = re.sub(r'<!-- CURSOR_SUMMARY -->.*?<!-- /CURSOR_SUMMARY -->', '', body or '', flags=re.DOTALL)
    body = re.sub(r'<!--.*?-->', '', body, flags=re.DOTALL)
    return re.sub(r'<div><a href=\"https://cursor\.com/agents.*', '', body).strip()


def summarise(prs: list[dict]) -> str:
    response = anthropic.Anthropic().beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        betas=['server-side-fallback-2026-07-01'],
        fallbacks='default',
        system=PROMPT,
        messages=[{'role': 'user', 'content': json.dumps(prs, indent=2)}],
    )
    if response.stop_reason != 'end_turn':
        sys.exit(f'Claude stopped with {response.stop_reason} (request {response._request_id})')
    return ''.join(block.text for block in response.content if block.type == 'text')


def main(old: str, new: str, clone: Path, out_dir: Path) -> None:
    prs = pull_requests(clone, old, new)
    if not prs:
        sys.exit(f'No merged pstack PRs between {old} and {new}')
    old_version, new_version = version(clone, old), version(clone, new)
    (out_dir / 'title.txt').write_text(f'pstack {old_version} → {new_version}: what Lauren changed')
    (out_dir / 'body.md').write_text(
        f'{summarise(prs)}\n\n---\n\n'
        f'[Cursor diff {old[:7]}...{new[:7]}](https://github.com/{REPO}/compare/{old}...{new}) · '
        f'{len(prs)} PRs · summarised by `{MODEL}`\n'
    )


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4]))

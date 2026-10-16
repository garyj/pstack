# /// script
# requires-python = ">=3.12"
# dependencies = ["anthropic>=1.15"]
# ///
"""Summarise the cursor/plugins PRs that changed pstack between two commits."""

import base64
import json
import re
import subprocess
import sys
from pathlib import Path

import anthropic

REPO = 'cursor/plugins'
MODEL = 'claude-sonnet-5-5'
PROMPT = Path(__file__).with_name('digest-prompt.md').read_text()


def gh(path: str) -> list | dict:
    out = subprocess.run(['gh', 'api', '--paginate', '--slurp', path], capture_output=True, text=True, check=True)
    pages = json.loads(out.stdout)
    return [item for page in pages for item in page] if isinstance(pages[0], list) else pages[0]


def version(sha: str) -> str:
    manifest = gh(f'repos/{REPO}/contents/pstack/.cursor-plugin/plugin.json?ref={sha}')
    return json.loads(base64.b64decode(manifest['content']))['version']


def commits_between(old: str, new: str) -> list[str]:
    shas = []
    for commit in gh(f'repos/{REPO}/commits?path=pstack&sha={new}&per_page=100'):
        if commit['sha'].startswith(old):
            return shas[::-1]
        shas.append(commit['sha'])
    sys.exit(f'{old} is not an ancestor of {new} in {REPO}')


def clean(body: str | None) -> str:
    body = re.sub(r'<!-- CURSOR_SUMMARY -->.*?<!-- /CURSOR_SUMMARY -->', '', body or '', flags=re.DOTALL)
    body = re.sub(r'<!--.*?-->', '', body, flags=re.DOTALL)
    return re.sub(r'<div><a href=\"https://cursor\.com/agents.*', '', body).strip()


def pull_requests(shas: list[str]) -> list[dict]:
    prs = {}
    for sha in shas:
        for pr in gh(f'repos/{REPO}/commits/{sha}/pulls'):
            if pr['merged_at'] and not pr['title'].startswith('chore(pstack): bump'):
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


def main(old: str, new: str, out_dir: Path) -> None:
    prs = pull_requests(commits_between(old, new))
    if not prs:
        sys.exit(f'No merged pstack PRs between {old} and {new}')
    old_version, new_version = version(old), version(new)
    (out_dir / 'title.txt').write_text(f'pstack {old_version} → {new_version}: what Lauren changed')
    (out_dir / 'body.md').write_text(
        f'{summarise(prs)}\n\n---\n\n'
        f'[Cursor diff {old[:7]}...{new[:7]}](https://github.com/{REPO}/compare/{old}...{new}) · '
        f'{len(prs)} PRs · summarised by `{MODEL}`\n'
    )


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], Path(sys.argv[3]))

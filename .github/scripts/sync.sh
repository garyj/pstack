#!/usr/bin/env bash
# Copy Cursor's Claude Code tree of pstack onto this repo and adapt it for APM.
# Usage: sync.sh <cursor/plugins checkout>
set -euo pipefail

tree="$1/harness/pstack/claude-code"
cd "$(git rev-parse --show-toplevel)"

# .apm/ covers skills and agents only. A new entry here is a new kind of plugin component, such as hooks or MCP.
expected=".claude-plugin LICENSE README.md agents docs plugin.json skills"
actual=$(find "$tree" -mindepth 1 -maxdepth 1 -printf '%f\n' | LC_ALL=C sort | xargs)
if [ "$actual" != "$expected" ]; then
	echo "::error::Cursor's Claude Code tree changed shape. Expected: $expected. Got: $actual"
	exit 1
fi
jq -e 'keys - ["$schema", "name", "displayName", "version", "description", "author", "homepage", "repository", "license", "logo", "keywords", "category", "tags"] == []' "$tree/plugin.json" >/dev/null ||
	{ echo "::error::Cursor's plugin.json declares components that .apm/ does not cover"; exit 1; }

for dir in skills agents docs; do
	rsync -a --delete "$tree/$dir/" "$dir/"
done
mkdir -p .claude-plugin
cp "$tree/.claude-plugin/plugin.json" .claude-plugin/
cp "$tree/README.md" "$tree/LICENSE" "$tree/plugin.json" .
uv run .github/scripts/adapt.py .

sed -i "s/^version: .*/version: $(jq -r .version plugin.json)/" apm.yml
rsync -a --delete agents/ .apm/agents/

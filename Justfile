_default:
	@just --list

PACKAGE_NAME := `jq -r '.name' package.json 2>/dev/null || echo comfydark`
PUBLISHER := `jq -r '.publisher' package.json 2>/dev/null || echo JensBech-Srensen`
VERSION := `jq -r '.version' package.json 2>/dev/null || echo 0.0.0`

clean:
	rm -f *.vsix

package: clean
	@if command -v vsce >/dev/null 2>&1; then \
	  vsce package --no-yarn; \
	else \
	  npx --yes @vscode/vsce package --no-yarn; \
	fi
	@ls -1 *.vsix 2>/dev/null | tail -n 1 | xargs -I {} bash -c 'echo "Built -> {}"'

publish-vsce:
	@if [ -z "$VSCE_TOKEN" ]; then echo "Error: VSCE_TOKEN not set" >&2; exit 1; fi
	@if command -v vsce >/dev/null 2>&1; then \
	  vsce publish --no-yarn; \
	else \
	  npx --yes @vscode/vsce publish --no-yarn; \
	fi

publish-ovsx:
	@if [ -z "$OVSX_TOKEN" ]; then echo "Error: OVSX_TOKEN not set" >&2; exit 1; fi
	@if command -v ovsx >/dev/null 2>&1; then \
	  ovsx publish --pat "$OVSX_TOKEN"; \
	else \
	  npx --yes ovsx publish --pat "$OVSX_TOKEN"; \
	fi

publish-all: publish-vsce publish-ovsx
	@echo "Published to both marketplaces."

bump-patch:
	@npm version patch --no-git-tag-version
	@just commit-and-tag

bump-minor:
	@npm version minor --no-git-tag-version
	@just commit-and-tag

bump-major:
	@npm version major --no-git-tag-version
	@just commit-and-tag

commit-and-tag:
	@new_version=$(jq -r '.version' package.json); \
	git add package.json; \
	git commit -m "chore: release v$$new_version"; \
	git tag v$$new_version; \
	echo "Tagged v$$new_version"; \
	echo "Next: git push && git push --tags"

release-patch: bump-patch publish-all

tokens-help:
	@echo "Create VSCE token: https://code.visualstudio.com/api/working-with-extensions/publishing-extension#get-a-personal-access-token"
	@echo "Create Open VSX token: https://open-vsx.org/user-settings/tokens"

version:
	@jq -r '.version' package.json 2>/dev/null || echo "Unknown"

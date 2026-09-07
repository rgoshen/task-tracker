#!/usr/bin/env bash
# Computes the next semver bump from Conventional Commits since the last
# git tag, bumps the version via `uv version`, and prepends a CHANGELOG.md
# entry grouped by Added/Fixed/Changed. Exits silently (no bump, no output)
# when no feat/fix/breaking commits are found since the last tag.
set -euo pipefail

repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"

last_tag=$(git describe --tags --abbrev=0 2>/dev/null || true)
if [[ -n "$last_tag" ]]; then
	range="${last_tag}..HEAD"
else
	range="HEAD"
fi

hashes=()
while IFS= read -r hash; do
	[[ -n "$hash" ]] && hashes+=("$hash")
done < <(git log "$range" --pretty=tformat:%H)

if [[ ${#hashes[@]} -eq 0 ]]; then
	exit 0
fi

bump_level=""
added=()
fixed=()
changed=()

# Matches an optional GitHub squash-merge bullet ("* " / "- ") followed by a
# Conventional Commits type, optional scope, and the breaking-change "!".
breaking_re='^(\* |- )?[a-z]+(\([a-z0-9_-]+\))?!:[[:space:]]*(.+)$'
feat_re='^(\* |- )?feat(\([a-z0-9_-]+\))?:[[:space:]]*(.+)$'
fix_re='^(\* |- )?fix(\([a-z0-9_-]+\))?:[[:space:]]*(.+)$'

for hash in "${hashes[@]}"; do
	message=$(git show -s --format=%B "$hash")
	subject=$(git show -s --format=%s "$hash")

	if [[ "$message" == *"BREAKING CHANGE:"* || "$subject" =~ $breaking_re ]]; then
		bump_level="major"
		changed+=("$subject")
		# ponytail: commit-level breaking short-circuits per-line feat/fix
		# scanning for this commit, so a squash-merged commit that bundles one
		# breaking change with unrelated feat/fix lines only surfaces the
		# breaking entry. Upgrade to per-line breaking detection if that
		# bundling turns out to happen in practice.
		continue
	fi

	while IFS= read -r line; do
		if [[ "$line" =~ $feat_re ]]; then
			[[ "$bump_level" == "major" ]] || bump_level="minor"
			added+=("${BASH_REMATCH[3]}")
		elif [[ "$line" =~ $fix_re ]]; then
			if [[ "$bump_level" != "major" && "$bump_level" != "minor" ]]; then
				bump_level="patch"
			fi
			fixed+=("${BASH_REMATCH[3]}")
		fi
	done <<<"$message"
done

if [[ -z "$bump_level" ]]; then
	exit 0
fi

uv version --bump "$bump_level" --no-sync >/dev/null
new_version=$(uv version --short)

changelog_file="CHANGELOG.md"
if [[ ! -f "$changelog_file" ]]; then
	printf '# Changelog\n\n' >"$changelog_file"
fi

entry=$(mktemp)
{
	printf '## [%s] - %s\n\n' "$new_version" "$(date +%Y-%m-%d)"
	if [[ ${#changed[@]} -gt 0 ]]; then
		printf '### Changed\n\n'
		for line in "${changed[@]}"; do printf -- '- %s\n' "$line"; done
		printf '\n'
	fi
	if [[ ${#added[@]} -gt 0 ]]; then
		printf '### Added\n\n'
		for line in "${added[@]}"; do printf -- '- %s\n' "$line"; done
		printf '\n'
	fi
	if [[ ${#fixed[@]} -gt 0 ]]; then
		printf '### Fixed\n\n'
		for line in "${fixed[@]}"; do printf -- '- %s\n' "$line"; done
		printf '\n'
	fi
} >"$entry"

{
	head -n 2 "$changelog_file"
	cat "$entry"
	tail -n +3 "$changelog_file"
} >"${changelog_file}.tmp"
mv "${changelog_file}.tmp" "$changelog_file"
rm -f "$entry"

echo "$new_version"

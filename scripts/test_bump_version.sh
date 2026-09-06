#!/usr/bin/env bash
# Self-check for bump-version.sh: seeds throwaway git repos with
# Conventional Commits and asserts the resulting bump level + CHANGELOG.md
# grouping. Run directly: ./scripts/test_bump_version.sh
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
bump_script="${script_dir}/bump-version.sh"
failures=0

assert_eq() {
  local expected=$1
  local actual=$2
  local msg=$3
  if [[ "$expected" != "$actual" ]]; then
    echo "FAIL: ${msg} (expected '${expected}', got '${actual}')" >&2
    failures=$((failures + 1))
  fi
}

assert_contains() {
  local file=$1
  local pattern=$2
  local msg=$3
  if ! grep -qF -- "$pattern" "$file"; then
    echo "FAIL: ${msg} (missing '${pattern}' in ${file})" >&2
    failures=$((failures + 1))
  fi
}

# Builds a throwaway git repo with a minimal uv project tagged v0.1.0.
new_scratch_repo() {
  local dir
  dir=$(mktemp -d)
  (
    cd "$dir"
    git init -q
    git config user.email "test@example.com"
    git config user.name "Test"
    cat > pyproject.toml <<'EOF'
[project]
name = "scratch"
version = "0.1.0"

[build-system]
requires = ["uv_build>=0.12.9,<0.13.0"]
build-backend = "uv_build"
EOF
    git add pyproject.toml
    git commit -q -m "chore: init"
    git tag v0.1.0
  )
  echo "$dir"
}

commit() {
  local dir=$1
  local message=$2
  (cd "$dir" && git commit -q --allow-empty -m "$message")
}

run_bump() {
  local dir=$1
  (cd "$dir" && "$bump_script")
}

test_patch_bump() {
  local dir output
  dir=$(new_scratch_repo)
  commit "$dir" "fix: correct off-by-one in due date sort"
  output=$(run_bump "$dir")
  assert_eq "0.1.1" "$output" "fix: commit should bump patch"
  assert_contains "${dir}/CHANGELOG.md" "### Fixed" "patch bump should add Fixed section"
  assert_contains "${dir}/CHANGELOG.md" "correct off-by-one in due date sort" "patch bump should list the fix"
  rm -rf "$dir"
}

test_minor_bump() {
  local dir output
  dir=$(new_scratch_repo)
  commit "$dir" "feat: add priority sort flag"
  output=$(run_bump "$dir")
  assert_eq "0.2.0" "$output" "feat: commit should bump minor"
  assert_contains "${dir}/CHANGELOG.md" "### Added" "minor bump should add Added section"
  rm -rf "$dir"
}

test_major_bump_via_bang() {
  local dir output
  dir=$(new_scratch_repo)
  commit "$dir" "feat!: drop legacy task id format"
  output=$(run_bump "$dir")
  assert_eq "1.0.0" "$output" "feat!: commit should bump major"
  assert_contains "${dir}/CHANGELOG.md" "### Changed" "major bump should add Changed section"
  rm -rf "$dir"
}

test_major_bump_via_footer() {
  local dir output
  dir=$(new_scratch_repo)
  commit "$dir" "$(printf 'fix: rename status enum\n\nBREAKING CHANGE: status values are now uppercase')"
  output=$(run_bump "$dir")
  assert_eq "1.0.0" "$output" "BREAKING CHANGE footer should bump major"
  rm -rf "$dir"
}

test_no_bump_for_chore() {
  local dir output
  dir=$(new_scratch_repo)
  commit "$dir" "chore: tidy up comments"
  output=$(run_bump "$dir")
  assert_eq "" "$output" "chore-only commit should not bump"
  if [[ -f "${dir}/CHANGELOG.md" ]]; then
    echo "FAIL: chore-only commit should not create CHANGELOG.md" >&2
    failures=$((failures + 1))
  fi
  rm -rf "$dir"
}

test_patch_bump
test_minor_bump
test_major_bump_via_bang
test_major_bump_via_footer
test_no_bump_for_chore

if [[ "$failures" -eq 0 ]]; then
  echo "All bump-version tests passed."
else
  echo "${failures} bump-version test(s) failed." >&2
  exit 1
fi

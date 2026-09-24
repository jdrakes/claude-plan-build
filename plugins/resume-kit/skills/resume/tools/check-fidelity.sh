#!/usr/bin/env bash
# Renderer regression test: render the example and compare its geometry
# against the committed baseline.
#
#   tools/check-fidelity.sh            check against examples/sample-resume.baseline.json
#   tools/check-fidelity.sh --update   rewrite that baseline from this render
#
# Run it after any edit to template.typ or components.typ. If it fails and
# the change was deliberate, --update and commit the new baseline with it.

set -euo pipefail

# Derived from this script's own location, not from $HOME, which says
# nothing about where the plugin is installed. -P resolves the symlinked
# plugin directory to the real one before applying "..", so a plugin reached
# through a symlink still finds its own fonts and template.
skill_dir="$(cd -P "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fixture="$skill_dir/examples/sample-resume.yaml"
baseline="$skill_dir/examples/sample-resume.baseline.json"

# The baseline is geometry from typst 0.15.1. A different version renders
# differently; that is not a regression. Regenerate with --update only when
# deliberately moving to a new typst.
expected_typst="0.15.1"

mode="--check"
if [[ "${1:-}" == "--update" ]]; then
  mode="--write"
fi

# Skipping is right on a contributor's laptop, which cannot be expected to
# carry one exact typst. It is never right on a runner that installs its own
# toolchain: there a skip means the workflow is broken, and exiting 0 would
# make the green tick mean nothing. RESUME_KIT_REQUIRE_FIDELITY=1 turns every
# skip below into a failure. CI sets it.
require="${RESUME_KIT_REQUIRE_FIDELITY:-}"

skip_or_fail() {  # message
  if [[ -n "$require" ]]; then
    echo "FAIL: $1" >&2
    echo "      RESUME_KIT_REQUIRE_FIDELITY is set, so this is a failure rather" >&2
    echo "      than a skip: the renderer went unchecked." >&2
    exit 1
  fi
  echo "SKIP: $1"
  exit 0
}

for tool in typst pdftotext python3; do
  command -v "$tool" >/dev/null 2>&1 || skip_or_fail "$tool not installed"
done

actual_typst="$(typst --version | awk '{print $2}')"
if [[ "$actual_typst" != "$expected_typst" ]]; then
  skip_or_fail "the baseline is pinned to typst $expected_typst, this host has $actual_typst"
fi

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

"$skill_dir/bin/build" "$fixture" -o "$work/sample-resume.pdf" >/dev/null
python3 "$skill_dir/tools/snapshot.py" "$work/sample-resume.pdf" "$mode" "$baseline"

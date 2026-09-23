#!/usr/bin/env python3
"""Scan skills/, agents/, docs/ and evals/ for leaked private references.

Real run:  python3 scripts/test_no_leaks.py
Self-test: python3 scripts/test_no_leaks.py --self-test
"""
import io
import os
import shutil
import sys
import tempfile
from pathlib import Path

LEAK_STRINGS = ["James", "jdrakes", "~/workspace", "knowledge-base", "jamesdrakes.com"]
SCAN_DIR_NAMES = {"skills", "agents", "docs", "evals"}
EXCLUDED_DIR_NAMES = {".claude-plugin", "scripts", ".git"}
EXCLUDED_FILE_NAMES = {"README.md"}


def find_scan_roots(repo_root):
    """Find every directory named skills/agents/docs/evals anywhere under
    repo_root, without descending into excluded directories."""
    roots = []
    for dirpath, dirnames, _ in os.walk(repo_root):
        dirnames[:] = [name for name in dirnames if name not in EXCLUDED_DIR_NAMES]
        if os.path.basename(dirpath) in SCAN_DIR_NAMES:
            roots.append(dirpath)
    return roots


def scan_file(path):
    """Return a list of (line_number, needle) hits in one file."""
    hits = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, start=1):
                for needle in LEAK_STRINGS:
                    if needle in line:
                        hits.append((line_number, needle))
    except (IsADirectoryError, PermissionError):
        pass
    return hits


def scan_repo(repo_root):
    """Return a list of (relative_path, line_number, needle) hits under
    repo_root's skills/, agents/, docs/ and evals/ directories."""
    all_hits = []
    for scan_root in find_scan_roots(repo_root):
        for dirpath, dirnames, filenames in os.walk(scan_root):
            dirnames[:] = [name for name in dirnames if name not in EXCLUDED_DIR_NAMES]
            for filename in sorted(filenames):
                if filename in EXCLUDED_FILE_NAMES:
                    continue
                file_path = os.path.join(dirpath, filename)
                relative_path = os.path.relpath(file_path, repo_root)
                for line_number, needle in scan_file(file_path):
                    all_hits.append((relative_path, line_number, needle))
    return all_hits


def run_scan(repo_root):
    hits = scan_repo(repo_root)
    for relative_path, line_number, needle in hits:
        print(f"{relative_path}:{line_number}: {needle}")
    return 1 if hits else 0


def run_self_test():
    temp_dir = tempfile.mkdtemp(prefix="test_no_leaks_")
    try:
        skills_dir = os.path.join(temp_dir, "skills", "example")
        os.makedirs(skills_dir)
        clean_path = os.path.join(skills_dir, "clean.md")
        bad_path = os.path.join(skills_dir, "bad.md")
        with open(clean_path, "w", encoding="utf-8") as handle:
            handle.write("This file has no private references.\n")
        with open(bad_path, "w", encoding="utf-8") as handle:
            handle.write("This file mentions jdrakes by name.\n")

        captured = io.StringIO()
        original_stdout = sys.stdout
        sys.stdout = captured
        try:
            exit_code = run_scan(temp_dir)
        finally:
            sys.stdout = original_stdout

        output = captured.getvalue()
        assert exit_code == 1, f"expected exit 1, got {exit_code}"
        assert "bad.md" in output, f"expected bad.md named in output, got: {output!r}"
        assert "clean.md" not in output, f"expected clean.md absent, got: {output!r}"
        print("self-test passed")
        return 0
    finally:
        shutil.rmtree(temp_dir)


def main():
    if "--self-test" in sys.argv:
        sys.exit(run_self_test())
    repo_root = Path(__file__).resolve().parent.parent
    sys.exit(run_scan(str(repo_root)))


if __name__ == "__main__":
    main()

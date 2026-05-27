#!/usr/bin/env python3
"""Lightweight public-release scan for FMG-Bench.

This is not a full security scanner. It catches common mistakes before a public
push: old product names, local absolute paths, known private artifact folders,
and obvious credential patterns.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
}

PATTERNS = {
    "old_product_name": re.compile(r"\bPetros\b|\bpetros\b"),
    "local_absolute_path": re.compile(r"/Users/|/home/"),
    "zenodo_commitment": re.compile(r"\bZenodo\b"),
    "private_key": re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"),
    "api_key_assignment": re.compile(
        r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{20,}"
    ),
}

ALLOWLIST = {
    # Environment variable names and examples are allowed when no value is present.
    ".env.example",
    "benchmark/openrouter.py",
    "dataset/scripts/push_to_hf.py",
    # Bibliography style mentions DOI mechanics; this is not a Zenodo commitment.
    "paper/acl_natbib.bst",
    # The scanner necessarily contains the patterns it searches for.
    "tools/release_scan.py",
}


def iter_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if is_gitignored(path):
            continue
        files.append(path)
    return files


def is_gitignored(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", rel.as_posix()],
        cwd=ROOT,
        check=False,
    )
    return result.returncode == 0


def is_text(path: Path) -> bool:
    try:
        path.read_text(encoding="utf-8")
        return True
    except UnicodeDecodeError:
        return False


def main() -> int:
    findings: list[tuple[str, str, int, str]] = []
    for path in iter_files():
        rel = path.relative_to(ROOT).as_posix()
        if rel in ALLOWLIST:
            continue
        if not is_text(path):
            continue
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), 1):
            for name, pattern in PATTERNS.items():
                if pattern.search(line):
                    findings.append((name, rel, lineno, line.strip()))

    if findings:
        print("Release scan found potential issues:\n")
        for name, rel, lineno, line in findings:
            print(f"{name}: {rel}:{lineno}: {line}")
        return 1

    print("Release scan passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

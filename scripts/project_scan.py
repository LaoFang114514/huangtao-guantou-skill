#!/usr/bin/env python3
"""项目快速摸底：目录结构、语言分布、构建清单、待办标记与体积异常文件。

用法：
    python project_scan.py [路径] [--depth 2] [--top 10]
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import Counter

SKIP_DIRS = {
    ".git", ".hg", ".svn", ".idea", ".vscode", "node_modules", "__pycache__",
    ".venv", "venv", "env", ".tox", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    "target", "build", "dist", "out", "bin", "obj", ".gradle", ".next", ".nuxt",
    "vendor", "coverage", ".cache", ".angular", ".terraform",
}

MANIFESTS = {
    "package.json": "Node.js",
    "pnpm-lock.yaml": "pnpm",
    "yarn.lock": "Yarn",
    "pom.xml": "Maven",
    "build.gradle": "Gradle",
    "build.gradle.kts": "Gradle",
    "settings.gradle": "Gradle",
    "requirements.txt": "pip",
    "pyproject.toml": "Python",
    "setup.py": "Python",
    "Pipfile": "pipenv",
    "Cargo.toml": "Rust",
    "go.mod": "Go",
    "CMakeLists.txt": "CMake",
    "Makefile": "Make",
    "composer.json": "PHP",
    "Gemfile": "Ruby",
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker Compose",
    "tsconfig.json": "TypeScript",
}

TEXT_EXT = {
    ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".java", ".kt", ".kts",
    ".go", ".rs", ".c", ".h", ".cc", ".cpp", ".hpp", ".cs", ".rb", ".php",
    ".swift", ".m", ".mm", ".vue", ".svelte", ".css", ".scss", ".less", ".html",
    ".md", ".json", ".yaml", ".yml", ".toml", ".ini", ".gradle", ".xml", ".sh",
    ".bash", ".bat", ".ps1", ".sql", ".proto", ".tex",
}

MARKERS = ("TODO", "FIXME", "XXX", "HACK")


def human_size(n: int) -> str:
    units = ("B", "KB", "MB", "GB", "TB")
    value = float(n)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return "%.1f %s" % (value, unit)
        value /= 1024
    return "%d B" % n


def count_markers(path: str) -> int:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return sum(fh.read().count(m) for m in MARKERS)
    except OSError:
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="项目快速摸底")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--depth", type=int, default=2, help="目录树展示层数")
    parser.add_argument("--top", type=int, default=10, help="语言分布展示条数")
    args = parser.parse_args()

    root = os.path.abspath(args.path)
    if not os.path.isdir(root):
        print("路径不存在或不是目录：%s" % root)
        return 2

    ext_counter: Counter = Counter()
    files = dirs = total_size = todos = 0
    large = []
    manifests = []
    tree = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")
        )
        rel = os.path.relpath(dirpath, root)
        level = 0 if rel == "." else rel.count(os.sep) + 1
        if level > args.depth:
            dirnames[:] = []
            continue
        if level > 0:
            tree.append("  " * (level - 1) + "|-- " + os.path.basename(dirpath) + "/")
            dirs += 1

        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            try:
                size = os.path.getsize(full)
            except OSError:
                continue
            files += 1
            total_size += size
            ext = os.path.splitext(name)[1].lower() or "(无扩展名)"
            ext_counter[ext] += 1
            if size >= 5 * 1024 * 1024:
                large.append((size, os.path.relpath(full, root)))
            if level <= 1 and name in MANIFESTS:
                manifests.append((name, MANIFESTS[name]))
            if size <= 1024 * 1024 and ext in TEXT_EXT:
                todos += count_markers(full)
            if level <= args.depth:
                tree.append("  " * level + "|-- " + name)

    print("== 概览 ==")
    print("路径      : %s" % root)
    print("文件 / 目录: %d / %d" % (files, dirs))
    print("总体积    : %s" % human_size(total_size))

    print("\n== 语言分布 ==")
    for ext, count in ext_counter.most_common(args.top):
        print("  %-12s %d" % (ext, count))

    print("\n== 构建 / 包管理 ==")
    if manifests:
        seen = set()
        for name, kind in manifests:
            if name in seen:
                continue
            seen.add(name)
            print("  %-20s %s" % (name, kind))
    else:
        print("  未发现常见清单文件，请手动确认构建方式")

    print("\n== 待办标记 ==")
    print("  TODO/FIXME/XXX/HACK: %d 处" % todos)

    print("\n== 体积异常文件（>= 5 MB） ==")
    if large:
        for size, path in sorted(large, reverse=True)[: args.top]:
            print("  %10s  %s" % (human_size(size), path))
    else:
        print("  无")

    print("\n== 目录结构（前 %d 层） ==" % args.depth)
    for line in tree[:200]:
        print("  " + line)
    if len(tree) > 200:
        print("  ... 其余 %d 项已省略" % (len(tree) - 200))

    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    raise SystemExit(main())

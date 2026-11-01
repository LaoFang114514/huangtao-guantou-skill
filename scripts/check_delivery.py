#!/usr/bin/env python3
"""交付前质量自检：文档、测试、调试残留、敏感信息、体积与构建产物。

用法：
    python check_delivery.py [路径] [--strict]

退出码：0 通过（可能含提示），1 发现阻断项（疑似密钥）。
"""
from __future__ import annotations

import argparse
import os
import re
import sys

SKIP_DIRS = {
    ".git", ".hg", ".svn", ".idea", ".vscode", "node_modules", "__pycache__",
    ".venv", "venv", "env", ".tox", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    ".gradle", ".next", ".nuxt", ".cache", ".angular", ".terraform",
}

ARTIFACT_DIRS = {"dist", "build", "target", "out", "coverage", "vendor"}

CODE_EXT = {
    ".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".vue", ".svelte",
    ".py", ".java", ".kt", ".go", ".rs", ".cs", ".rb", ".php", ".swift",
}

DEBUG_PATTERNS = [
    (re.compile(r"\bconsole\.(log|debug|trace)\s*\("), "console.log"),
    (re.compile(r"\bdebugger\s*;?"), "debugger"),
    (re.compile(r"^\s*print\s*\(", re.M), "print("),
    (re.compile(r"\bSystem\.out\.print"), "System.out.print"),
    (re.compile(r"\bfmt\.Print"), "fmt.Print"),
]

SECRET_RE = re.compile(
    r"(?i)\b(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|"
    r"client[_-]?secret|password|passwd)\b\s*[:=]\s*['\"][^'\"\s]{8,}['\"]"
)

SECRET_FILES = re.compile(r"(^\.env($|\.)|(^|/)id_rsa$|\.pem$|\.p12$|\.key$)", re.I)

TEXT_EXT = CODE_EXT | {
    ".json", ".yaml", ".yml", ".toml", ".ini", ".properties", ".xml", ".sh",
    ".bash", ".bat", ".ps1", ".sql", ".md", ".gradle", ".conf",
}


def human_size(n: int) -> str:
    units = ("B", "KB", "MB", "GB")
    value = float(n)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return "%.1f %s" % (value, unit)
        value /= 1024
    return "%d B" % n


def read_text(path: str, limit: int = 1024 * 1024):
    try:
        if os.path.getsize(path) > limit:
            return None
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except OSError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="交付前质量自检")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--strict", action="store_true", help="把提示项升级为阻断项")
    args = parser.parse_args()

    root = os.path.abspath(args.path)
    if not os.path.isdir(root):
        print("路径不存在或不是目录：%s" % root)
        return 2

    passed, warned, failed = [], [], []
    artifacts = set()
    has_readme = False
    has_tests = False
    has_git = os.path.isdir(os.path.join(root, ".git"))
    large = []
    secrets = []
    debug_hits = []
    todos = 0

    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        level = 0 if rel_dir == "." else rel_dir.count(os.sep) + 1

        for d in dirnames:
            low = d.lower()
            if low in ARTIFACT_DIRS:
                artifacts.add(os.path.join(rel_dir, d) if level else d)
            if low in ("test", "tests", "spec", "__tests__", "testcases"):
                has_tests = True

        dirnames[:] = sorted(
            d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")
        )

        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            try:
                size = os.path.getsize(full)
            except OSError:
                continue

            low = name.lower()
            ext = os.path.splitext(low)[1]

            if level == 0 and low.startswith("readme"):
                has_readme = True
            if re.search(r"(^test_|_test\.|\.test\.|\.spec\.)", low):
                has_tests = True
            if size >= 5 * 1024 * 1024:
                large.append((size, rel))
            if SECRET_FILES.search(rel.replace("\\", "/")) and not low.endswith(
                (".env.example", ".env.sample", ".env.template")
            ):
                secrets.append((rel, "敏感文件"))
                continue
            if ext not in TEXT_EXT:
                continue

            text = read_text(full)
            if text is None:
                continue
            todos += text.count("TODO") + text.count("FIXME")
            if ext in CODE_EXT:
                for pattern, label in DEBUG_PATTERNS:
                    if pattern.search(text):
                        debug_hits.append((rel, label))
                        break
            if ext in TEXT_EXT:
                hit = SECRET_RE.search(text)
                if hit:
                    secrets.append((rel, "疑似硬编码 %s" % hit.group(1)))

    (passed if has_readme else warned).append(
        "根目录 README" if has_readme else "根目录缺少 README"
    )
    (passed if has_tests else warned).append(
        "测试用例" if has_tests else "未发现测试目录或用例"
    )
    (passed if has_git else warned).append(
        "Git 仓库" if has_git else "未检测到 .git，注意版本管理"
    )

    print("== 交付自检：%s ==\n" % root)
    for item in passed:
        print("  [PASS] %s" % item)
    for item in warned:
        print("  [WARN] %s" % item)

    if debug_hits:
        print("\n[WARN] 调试残留 %d 处：" % len(debug_hits))
        for rel, label in debug_hits[:10]:
            print("  - %s  (%s)" % (rel, label))
        if len(debug_hits) > 10:
            print("  ... 其余 %d 处已省略" % (len(debug_hits) - 10))

    if artifacts:
        print("\n[WARN] 构建产物目录：%s" % "、".join(sorted(artifacts)[:8]))

    if large:
        print("\n[WARN] 大文件（>= 5 MB）：")
        for size, rel in sorted(large, reverse=True)[:8]:
            print("  - %s  %s" % (human_size(size), rel))

    if secrets:
        failed.append("疑似敏感信息")
        print("\n[FAIL] 疑似敏感信息 %d 处：" % len(secrets))
        for rel, why in secrets[:10]:
            print("  - %s  (%s)" % (rel, why))
        print("  建议：移除密钥并轮换，改用环境变量或密钥管理服务。")

    print("\n待办标记：TODO/FIXME %d 处" % todos)

    if args.strict and warned:
        failed.append("--strict 模式")

    print("\n结论：%s" % ("不通过" if failed else "通过"))
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    raise SystemExit(main())

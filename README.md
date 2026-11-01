# 黄桃罐头 · 通用编程辅助

> 面向任意语言与技术栈的编程任务技能包：摸底 → 方案 → 实现 → 验证 → 交付。

## 特性

- **项目摸底**：一条命令输出目录结构、语言分布、构建清单、待办标记与体积异常文件。
- **交付自检**：检查文档、测试、调试残留、硬编码密钥、大文件与构建产物。
- **流程资产**：工作流、编码约定、排错手册三份参考文档，覆盖从读代码到发版的通用环节。
- **终端横幅**：内置 5 套 80 列等宽横幅资源，用于 CLI 首屏与文档占位。

## 快速开始

```bash
# 项目摸底
python scripts/project_scan.py .

# 交付自检
python scripts/check_delivery.py .

# 严格模式：提示项同样视为不通过
python scripts/check_delivery.py . --strict
```

两个脚本均为标准库实现，无第三方依赖，适用于本地与 CI。

## 目录结构

```
黄桃罐头/
├── README.md                  ← 本文件
├── SKILL.md                   ← 技能主入口
├── _meta.json                 ← 元数据
├── assets/
│   └── banners/               ← 终端横幅 01~05.txt
├── references/
│   ├── workflow.md            ← 工作流详解
│   ├── conventions.md         ← 编码约定
│   ├── debugging.md           ← 排错手册
│   └── brand-banner.md        ← 横幅使用规则
└── scripts/
    ├── project_scan.py        ← 项目摸底
    └── check_delivery.py      ← 交付自检
```

## 环境要求

- Python 3.8 及以上（脚本）
- Windows 下可用 `py -3` 代替 `python`
- 无第三方依赖

## 使用建议

1. 接到改动类任务，先跑 `project_scan.py`，结合 README 与清单确认技术栈。
2. 按 `references/workflow.md` 的五步推进，方案先行、改动最小。
3. 交付前跑 `check_delivery.py`，清理调试残留与敏感信息。

## 版本

- **1.3.0** — 增加项目摸底与交付自检脚本，补充流程/约定/排错参考文档。
- **1.2.0** — 整理横幅资源至 `assets/banners/`，补充使用规则。
- **1.1.0** — 统一工作流与编码约定。

## 许可

MIT License，详见 [LICENSE](LICENSE)。

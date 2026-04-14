# grad-app-toolkit

![Version](https://img.shields.io/badge/version-1.0-blue)
![Platform](https://img.shields.io/badge/platform-Codex%20%7C%20Claude%20CLI%20%7C%20Trae-success)

面向中国留学生的 AI 驱动硕博申请全流程工具箱。

它采用“阶段路由 + 状态持久化”的原子架构，不把所有逻辑塞进一个大 prompt，而是通过 `SKILL.md` / `.traerules` 自动识别申请阶段，结合 `memory_manager.py` 维护共享状态，让 Claude CLI、Trae IDE、Codex 等 AI 编程助手在同一份申请语境中持续工作，输出一致、可追踪、可校验的指导。

## 核心能力

- 语言训练：IELTS / TOEFL 口语模拟、写作评分、学习计划
- 背景分析：背景定位、CV 重构、现实校准
- 导师检索：4D 导师评分矩阵，支持 US / EU / HK-SG / CN 区域适配
- 套磁支持：三段式 cold pitch、跟进协议
- 文书架构：PS / SOP / Research Proposal 双轨指导
- 面试与 offer：委员会 / 面板模拟面试、offer negotiation guide

## 核心架构

- 6 个阶段知识底座 + 1 个共享记忆层
- `candidate_memory.json` 配合 JSON Schema 严格校验
- 文件锁 + 原子写入，保障并发安全
- 参考数据来自 CSV ground-truth，便于校准判断
- 全部基于 Python 标准库实现，零外部依赖

## 6 阶段流水线

| 阶段 | 知识底座 | 覆盖内容 |
|---|---|---|
| Stage 0 | `stage0_language_coach.md` | IELTS / TOEFL 口语模拟、写作评分、学习计划 |
| Stage 1 | `stage1_profile_analyzer.md` | 背景定位、CV 重构（STAR 法则）、现实校准（MRes 保底 / RA 间隔年） |
| Stage 2 | `stage2_lab_detective.md` | 4D 导师评分矩阵（Fit / Activity / Feasibility / Risk），US / EU / HK-SG / CN 区域适配 |
| Stage 3 | `stage3_cold_pitch.md` | 套磁信 3 段结构（Hook / Value / CTA）、跟进协议 |
| Stage 4 | `stage4_sop_architect.md` | PS / SOP（4 段式）+ Research Proposal（Research Gap + Gantt Chart）双轨制 |
| Stage 5 & 6 | `stage5_6_defense_and_offer.md` | North America committee / Europe panel mock interview + offer negotiation templates |

## 技术栈

| 组件 | 技术选型 |
|---|---|
| 状态管理 | Python CLI (`memory_manager.py`) — init / read / validate / update / backup / bootstrap |
| 数据合约 | JSON Schema (`memory_contract.json`) — `additionalProperties: false`，严格类型校验 |
| 并发安全 | 文件锁 (`candidate_memory.json.lock`) + 原子写入 (`tempfile` + `os.replace`) |
| 参考数据 | CSV ground-truth（中国学术头衔层级、欧洲 PhD 薪资 TVoD、美国 stipend 地区对照） |
| 测试 | 35 个 `unittest`（内存管理、协议一致性、Shell 诊断） |
| CI | GitHub Actions (`windows-latest`, Python 3.11 / 3.12) |

## 设计原则

- 不把所有知识塞进一个 prompt
- 不代写掺水履历
- 不造假数据
- 不背书中介话术
- 所有指导都服务于“学生向独立研究者”的真实转型

## 使用方式

### Claude CLI

- 打开仓库根目录后，`SKILL.md` 会作为路由分发入口
- 先运行 `python scripts/memory_manager.py bootstrap`
- 需要检查状态时运行 `python scripts/memory_manager.py validate`
- 需要读取当前共享状态时运行 `python scripts/memory_manager.py read`

### Trae IDE

- 直接用 Trae 打开本项目文件夹
- `.traerules` 会接管阶段路由和共享状态读取逻辑

### Codex / 其他 AI 编程助手

- `SKILL.md` 负责阶段识别与知识底座分发
- 所有阶段都通过 `references/` 中的原子知识文件提供支持

## 项目结构

```text
grad-app-toolkit/
├── SKILL.md
├── .claude-plugin
├── .traerules
├── README.md
├── assets/
│   ├── memory_contract.json
│   ├── memory_schema.json
│   └── ground_truth/
├── references/
├── scripts/
│   ├── memory_manager.py
│   └── shell_diagnostics.py
├── tests/
└── .github/workflows/ci.yml
```

## 验证与排障

- 仓库使用 GitHub Actions 在 `windows-latest` 上运行单测与状态校验
- If you want to verify the shell runtime, run `python scripts/shell_diagnostics.py`
- 如果你只关心共享状态是否合规，可以运行 `python scripts/memory_manager.py validate`

## 当前状态

- 代码质量：本轮审核后修复了 6 个 HIGH、5 个 MEDIUM、2 个 LOW 问题
- 测试覆盖：`35/35` 全部通过
- Git 状态：所有修改在工作区，未提交

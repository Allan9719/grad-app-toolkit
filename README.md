# grad-app-toolkit

![Version](https://img.shields.io/badge/version-1.0-blue)
![Platform](https://img.shields.io/badge/platform-Codex%20%7C%20Claude%20CLI%20%7C%20Trae-success)

面向中国留学生的 AI 驱动硕博申请工具箱。

它把申请流程拆成 6 个阶段知识底座 + 1 个共享记忆层，通过 `SKILL.md` / `.traerules` 路由到对应阶段，并用 `scripts/memory_manager.py` 维护 `candidate_memory.json`，让 Claude CLI、Trae IDE、Codex 等助手在同一份申请语境里持续工作。

## 一句话价值

- 少问重复问题
- 少写通用废话
- 让申请指导始终围绕当前阶段和真实背景展开

## 6 阶段流水线

| 阶段 | 作用 | 知识底座 |
|---|---|---|
| Stage 0 | 语言训练 | `stage0_language_coach.md` |
| Stage 1 | 背景分析与 CV 重构 | `stage1_profile_analyzer.md` |
| Stage 2 | 导师检索与风险排雷 | `stage2_lab_detective.md` |
| Stage 3 | 套磁支持 | `stage3_cold_pitch.md` |
| Stage 4 | SOP / PS / Research Proposal | `stage4_sop_architect.md` |
| Stage 5 & 6 | 面试压测与 offer 谈判 | `stage5_6_defense_and_offer.md` |

## 核心文件

- `SKILL.md`：Claude CLI 的路由入口
- `.traerules`：Trae IDE 的系统规则
- `scripts/memory_manager.py`：共享状态管理 CLI
- `assets/memory_contract.json`：状态合约与校验规则
- `references/`：6 个阶段的原子知识底座
- `tests/`：协议一致性、内存管理、Shell 诊断测试
- `CHANGELOG.md`：版本记录与发布说明
- `.github/workflows/ci.yml`：Windows CI

## 快速开始

1. `python scripts/memory_manager.py bootstrap`
2. `python scripts/memory_manager.py validate`
3. 在 Claude CLI、Trae IDE 或 Codex 中打开仓库，按阶段使用对应命令或路由

## 安全边界

- 不代写掺水履历
- 不造假数据
- 不背书中介话术
- 所有指导都服务于“学生向独立研究者”的真实转型

## 当前状态

- `35/35` 测试通过
- 共享记忆合约已验证
- GitHub Actions 已接入 Windows CI

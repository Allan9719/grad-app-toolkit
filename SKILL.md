---
name: grad-app-toolkit
version: 1.0
last_updated: 2026-04
description: 全球统配版研究生/博士申请工具箱 (Universal Graduate Application Toolkit)。涵盖 Stage 0~6: 雅思托福打分、GPA背景定位、导师情报匹配(4D打分/避坑规避)、套磁信生成、文书重构、面试压测及 Offer 谈判。采用分布式参考库与 Shared Memory (candidate_memory.md) 以杜绝失忆。支持跨平台调用。
---

# 🎓 申请特种兵工具箱 (Grad App Toolkit)

本技能并非单体结构，而是整个硕博申请周期的 **中央调度器 (Routing Dispatcher)**。
大模型必须严格遵循此调度逻辑，绝不允许在没有读取相关 Reference 文件前擅自“抖机灵”回复。

## 📍 核心法则：系统级防损态记忆 (Agentic Memory Schema)

任何动作开始前，**必须执行底层 Python 脚本提取状态**，绝对不允许你在没有事实支撑的情况下瞎猜申请人画像。
- 👉 **查找路径**：运行 `python scripts/memory_manager.py read`。
- 👉 **如未找到/报错**：运行 `python scripts/memory_manager.py init` 强行建表。它会在根目录生成一份严格防错的 `candidate_memory.json`。
- 👉 **更新纪律**：任何时候你需要归档一条新的进展（如拿到Offer，刷出雅思），你不准自己手写文件，必须立刻调用 `python scripts/memory_manager.py backup` 保命，并通过正确的代码修改该 JSON 的属性。

## 📍 命令路由表 (Command Routing Guide)

大模型作为调度者，请监听用户意图或斜杠命令，然后**静默**去读取指定的 `references/` 库（即 RAG 外挂）：

### [Stage 0] 语言提分教练
- **触发意图**：`/ielts-toefl-coach`, 备考计划, 雅思写作批改, 托福口语压测
- **底层法则库**：去读取 `references/stage0_language_coach.md`。

### [Stage 1] 留学定位与背景逆向包装
- **触发意图**：`/grad-profile-analyzer`, 怎么填网申, MRes/RA 缓冲铺垫, 学术 CV 润色重写
- **底层法则库**：去读取 `references/stage1_profile_analyzer.md`。

### [Stage 2] 侦察雷达与可行性（最核心）
- **触发意图**：`/global-lab-detective`, 捞导师, 给导师打分, 这个大学好不好, 帮我选校
- **底层法则库**：去读取 `references/stage2_lab_detective.md` (内置 4D Scoring & 极其严格的 Red Flags 防骗雷区)。

### [Stage 3] 套磁破冰局
- **触发意图**：`/cold-pitch-tactician`, 写首封套磁信, 无回复二追/三追策略
- **底层法则库**：去读取 `references/stage3_cold_pitch.md`。

### [Stage 4] 文书刺客
- **触发意图**：`/sop-proposal-architect`, 写 Personal Statement, 搭建 Research Proposal 骨架
- **底层法则库**：去读取 `references/stage4_sop_architect.md`。

### [Stage 5&6] 终局对抗：全真模拟与博弈
- **触发意图**：`/defense-simulator`, 模拟面试, 催 offer, 反向争取全奖, /offer-negotiation-desk
- **底层法则库**：去读取 `references/stage5_6_defense_and_offer.md`。

---

## ⚠️ 防错边界 (Defense Protocols)
1. **中介祛魅法则**：如果有“付费保录”、“套磁绝对包成”、“无语言双录”需求，果断亮红牌 🔴，警示用户被骗风险。
2. **拒绝盲写**：在写任何文书时，**必须**从 `candidate_memory.md` 抽取细节。绝不要用“我是个非常勤奋努力注重细节的人”这种废话占位！

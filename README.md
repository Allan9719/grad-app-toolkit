# grad-app-toolkit

[![Version](https://img.shields.io/badge/version-2.0-blue)](./CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-35%2F35-brightgreen)](./tests/)
[![Platform](https://img.shields.io/badge/platform-Claude%20CLI%20%7C%20Trae%20%7C%20Codex-success)](./SKILL.md)
[![CI](https://img.shields.io/badge/CI-Windows-blueviolet)](./.github/workflows/ci.yml)

AI-powered graduate application toolkit for Chinese students. Covers the entire journey from language prep to offer negotiation, with a shared memory layer that keeps every AI session context-aware.

---

## Why This Exists

Applying for a Master's or PhD abroad involves dozens of repetitive conversations with AI assistants. Every new session, you re-explain your GPA, your target region, your publications. This toolkit eliminates that friction:

- **Stateful memory** - Your profile lives in a structured JSON file, not in chat history
- **Stage routing** - Each phase of the application has a dedicated knowledge base
- **Cross-platform** - Works in Claude CLI, Trae IDE, and Codex with the same data

## The 6-Stage Pipeline

```
Stage 0          Stage 1           Stage 2           Stage 3          Stage 4           Stage 5&6
Language ────> Profile ────────> Supervisor ──────> Cold Pitch ────> SOP/PS/RP ──────> Interview &
Coach            Analyzer          Detective                           Architect          Offer
```

| Stage | What It Does | Trigger |
|-------|-------------|---------|
| **0** Language Coach | IELTS/TOEFL mock grading, study plans, writing correction | "雅思怎么上7", "帮我批改大作文" |
| **1** Profile Analyzer | GPA positioning, CV rewriting, application strategy | "我这个背景能申哪", "帮我改CV" |
| **2** Lab Detective | 4D supervisor scoring, red-flag detection, fit analysis | "这个导师怎么样", "帮我选校" |
| **3** Cold Pitch | Outreach email drafting, follow-up strategies | "帮我写套磁信", "导师没回怎么办" |
| **4** SOP Architect | Personal Statement, Research Proposal structure | "帮我写PS", "Research Proposal怎么搭" |
| **5&6** Defense & Offer | Mock interviews, offer comparison, funding negotiation | "模拟面试", "怎么催offer" |

## Shared Memory System

The core of this toolkit is `candidate_memory.json` - a structured state file that persists your profile across sessions:

```
candidate_memory.json
├── static_profile        # GPA, institution, funding constraints
├── academic_arsenal      # Language scores, publications, skills
├── risk_thresholds       # Dealbreakers, preferred regions
└── pipeline_status       # Progress tracker for all 6 stages
```

All mutations go through `scripts/memory_manager.py`, which auto-backs up before every write and validates against a JSON Schema contract.

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/Allan9719/grad-app-toolkit.git
cd grad-app-toolkit

# 2. Bootstrap - creates and validates your memory file
python scripts/memory_manager.py bootstrap

# 3. Verify everything is healthy
python scripts/memory_manager.py validate

# 4. Open in your AI assistant and start applying
```

### Memory Manager Commands

```bash
python scripts/memory_manager.py init                    # Create empty memory file
python scripts/memory_manager.py bootstrap               # Init + validate in one step
python scripts/memory_manager.py read                    # Print current state
python scripts/memory_manager.py validate                # Check against contract schema
python scripts/memory_manager.py update <path> <value>   # Update a field (auto-backup)
# Example: python scripts/memory_manager.py update static_profile.metrics.gpa 3.85
```

## Project Structure

```
grad-app-toolkit/
├── SKILL.md                          # Claude CLI skill entry point
├── .traerules                        # Trae IDE system rules
├── .claude-plugin                    # Plugin command registry
├── candidate_memory.json             # Your persistent profile (auto-generated)
├── scripts/
│   ├── memory_manager.py             # State management CLI
│   └── shell_diagnostics.py          # Shell environment diagnostics
├── references/                       # Stage knowledge bases (the "brain")
│   ├── stage0_language_coach.md
│   ├── stage1_profile_analyzer.md
│   ├── stage2_lab_detective.md
│   ├── stage3_cold_pitch.md
│   ├── stage4_sop_architect.md
│   └── stage5_6_defense_and_offer.md
├── assets/
│   ├── memory_contract.json          # JSON Schema for memory validation
│   ├── memory_schema.json            # Legacy schema
│   ├── memory_template.md            # Template for new profiles
│   └── ground_truth/                 # Reference data (stipends, salaries)
├── tests/                            # 35 tests: protocol, memory, shell
├── docs/
│   └── verification_and_shell_troubleshooting.md
├── .github/workflows/ci.yml          # Windows CI pipeline
└── CHANGELOG.md
```

## Safety Boundaries

This toolkit will **never**:

- Ghostwrite fabricated credentials or inflated CVs
- Generate fake data or test scores
- Endorse predatory agency rhetoric or "guaranteed admission" scams
- Produce generic filler like "I am a diligent and detail-oriented student"

Every piece of advice is designed to support your genuine transition from student to independent researcher.

## Tech Stack

- **Language**: Python 3.11+
- **State format**: JSON with JSON Schema validation
- **Concurrency**: File-based locking for multi-process safety
- **CI**: GitHub Actions on Windows
- **Testing**: pytest (35 tests, protocol consistency + memory management)

## License

This project is intended for personal, educational use. See repository for details.

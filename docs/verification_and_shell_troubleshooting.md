# Verification And Shell Troubleshooting

## Verified Baseline

This repository currently has two independent facts that should be treated separately:

1. Manual verification on the machine succeeded:
   - `powershell.exe -NoProfile` opens normally.
   - `python -m unittest discover -s E:\skills-library\grad-app-toolkit\tests -v` passes when run manually.
2. Codex shell execution in this session may still fail before commands start, including failures that surface as PowerShell startup errors such as `8009001d`.

Because of that split, a Codex shell startup failure must not be treated as evidence that the repository is broken.

## How To Interpret Failures

- If manual test execution passes but Codex shell startup fails, classify the issue as a shell host/runtime problem.
- If both manual execution and Codex execution fail, investigate the repository or Python environment.
- If `pwsh.exe` works but `powershell.exe` fails, prefer PowerShell 7 and treat legacy Windows PowerShell as the unstable host.
- If only `cmd.exe` works, use it as a temporary fallback for diagnostics and test launching.

## Recommended Diagnostics

Run the repo-local diagnostics script:

```bash
cd E:\skills-library\grad-app-toolkit
python scripts/shell_diagnostics.py
```

JSON output is also available:

```bash
cd E:\skills-library\grad-app-toolkit
python scripts/shell_diagnostics.py --json
```

Or use an absolute path from any working directory:

```bash
python E:\skills-library\grad-app-toolkit\scripts\shell_diagnostics.py
```

This script probes three shell hosts:

- `powershell.exe -NoProfile -NonInteractive -Command "$PSVersionTable.PSVersion"`
- `pwsh.exe -NoProfile -NonInteractive -Command "$PSVersionTable.PSVersion"`
- `cmd.exe /c ver`

It also runs the repository test suite directly through the current Python interpreter:

```bash
python -m unittest discover -s tests -v
```

And it additionally attempts to launch the same test suite through each shell host so you can tell:

- which host is merely installed,
- which host can start successfully,
- and which host can actually carry the repository test command end to end.

## Memory State Health Check

If you need to confirm that `candidate_memory.json` still matches the schema contract, run:

```bash
python scripts/memory_manager.py bootstrap
```

If the file already exists and you only want to re-check it, run:

```bash
python scripts/memory_manager.py validate
```

`bootstrap` creates the file if it is missing and then validates it. `validate` only checks an existing file. Both commands report missing keys, unexpected keys, enum violations, string length violations, and type mismatches against `assets/memory_contract.json`.

The write path also creates a transient `candidate_memory.json.lock` while a process is mutating shared memory. The lock is removed automatically after a successful write, and stale locks older than five minutes are reclaimed on the next write attempt.

## Temporary Workarounds

- Prefer `pwsh.exe` if it is healthy.
- Fall back to `cmd.exe` if PowerShell startup is unstable.
- If all shell probes fail but direct manual execution still works, escalate the problem as a Codex host/runtime issue rather than changing repository code.

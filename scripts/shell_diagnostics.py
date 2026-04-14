import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]

TEST_COMMAND: list[str] = [
    sys.executable,
    "-m",
    "unittest",
    "discover",
    "-s",
    str(ROOT_DIR / "tests"),
    "-v",
]

HOST_PROBES: dict[str, list[str]] = {
    "powershell": [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        "$PSVersionTable.PSVersion",
    ],
    "pwsh": [
        "pwsh.exe",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        "$PSVersionTable.PSVersion",
    ],
    "cmd": [
        "cmd.exe",
        "/c",
        "ver",
    ],
}


def _command_to_windows_string(command: list[str]) -> str:
    return subprocess.list2cmdline(command)


def run_command(command: list[str], timeout: int = 20) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=ROOT_DIR,
            check=False,
        )
    except FileNotFoundError:
        return {
            "ok": False,
            "exit_code": None,
            "stdout": "",
            "stderr": "executable not found",
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "exit_code": None,
            "stdout": "",
            "stderr": f"timed out after {timeout} seconds",
        }
    except Exception as error:  # pragma: no cover - defensive wrapper
        return {
            "ok": False,
            "exit_code": None,
            "stdout": "",
            "stderr": str(error),
        }

    return {
        "ok": completed.returncode == 0,
        "exit_code": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def probe_hosts() -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for host_name, command in HOST_PROBES.items():
        executable = command[0]
        results[host_name] = {
            "available": shutil.which(executable) is not None,
            "command": command,
            "probe": run_command(command),
        }
    return results


def run_tests_direct() -> dict[str, Any]:
    return {
        "command": TEST_COMMAND,
        "result": run_command(TEST_COMMAND, timeout=120),
    }


def run_tests_via_hosts() -> dict[str, dict[str, Any]]:
    test_command_string = _command_to_windows_string(TEST_COMMAND)
    host_test_commands: dict[str, list[str]] = {
        "powershell": [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            test_command_string,
        ],
        "pwsh": [
            "pwsh.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            test_command_string,
        ],
        "cmd": [
            "cmd.exe",
            "/c",
            test_command_string,
        ],
    }

    results: dict[str, dict[str, Any]] = {}
    for host_name, command in host_test_commands.items():
        results[host_name] = {
            "command": command,
            "result": run_command(command, timeout=120),
        }
    return results


def _get_hosts(results: dict[str, Any]) -> dict[str, Any]:
    return results.get("hosts", results)


def _safe_nested_get(data: Any, *keys: str, default: Any = None) -> Any:
    """Safely navigate nested dicts without AttributeError on malformed data."""
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        if key not in current:
            return default
        current = current[key]
    return current


def recommend(results: dict[str, Any]) -> str:
    hosts = _get_hosts(results)
    host_test_runs: dict[str, Any] = results.get("host_test_runs", {})

    pwsh_test_ok = bool(_safe_nested_get(host_test_runs, "pwsh", "result", "ok", default=False))
    powershell_test_ok = bool(_safe_nested_get(host_test_runs, "powershell", "result", "ok", default=False))
    cmd_test_ok = bool(_safe_nested_get(host_test_runs, "cmd", "result", "ok", default=False))

    if pwsh_test_ok:
        return "pwsh.exe is healthy; prefer PowerShell 7 over legacy Windows PowerShell."
    if powershell_test_ok and cmd_test_ok:
        return (
            "legacy powershell.exe is healthy and can launch the repo tests successfully; "
            "cmd.exe is also available as a fallback if Codex still fails to launch PowerShell."
        )
    if powershell_test_ok:
        return "legacy powershell.exe is healthy and can launch the repo tests successfully."
    if cmd_test_ok:
        return (
            "cmd.exe can launch the repo tests successfully; "
            "if Codex still fails to launch PowerShell, use cmd.exe as the temporary fallback."
        )
    if _safe_nested_get(hosts, "pwsh", "probe", "ok", default=False):
        return "pwsh.exe is installed and responsive; prefer PowerShell 7 over legacy Windows PowerShell."
    if (
        _safe_nested_get(hosts, "powershell", "probe", "ok", default=False)
        and _safe_nested_get(hosts, "cmd", "probe", "ok", default=False)
    ):
        return (
            "powershell.exe is healthy locally and cmd.exe is also available; "
            "if Codex still fails to launch PowerShell, use cmd.exe as the temporary fallback."
        )
    if _safe_nested_get(hosts, "powershell", "probe", "ok", default=False):
        return "legacy powershell.exe is healthy locally."
    if _safe_nested_get(hosts, "cmd", "probe", "ok", default=False):
        return "cmd.exe is healthy; use cmd as a temporary fallback when PowerShell host startup is unstable."
    return "No shell host probe succeeded. Treat this as a host/runtime issue rather than a repo failure."


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Probe shell hosts and run the repo's unit tests without relying on Codex shell heuristics.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Only probe shell hosts.",
    )
    args = parser.parse_args(argv)

    host_results = probe_hosts()
    payload: dict[str, Any] = {
        "root_dir": str(ROOT_DIR),
        "hosts": host_results,
    }

    if not args.skip_tests:
        payload["direct_python_tests"] = run_tests_direct()
        payload["host_test_runs"] = run_tests_via_hosts()

    payload["recommendation"] = recommend(payload)

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    print("== Shell Host Diagnostics ==")
    for host_name, details in host_results.items():
        status = "OK" if details["probe"]["ok"] else "FAIL"
        print(f"- {host_name}: {status}")
        print(f"  command: {' '.join(details['command'])}")
        if details["probe"]["stdout"]:
            print(f"  stdout: {details['probe']['stdout']}")
        if details["probe"]["stderr"]:
            print(f"  stderr: {details['probe']['stderr']}")

    if not args.skip_tests:
        test_result = payload["direct_python_tests"]["result"]
        test_status = "OK" if test_result["ok"] else "FAIL"
        print(f"- direct_python_tests: {test_status}")
        print(f"  command: {' '.join(payload['direct_python_tests']['command'])}")
        if test_result["stdout"]:
            print(f"  stdout: {test_result['stdout']}")
        if test_result["stderr"]:
            print(f"  stderr: {test_result['stderr']}")

        for host_name, details in payload["host_test_runs"].items():
            host_test_status = "OK" if details["result"]["ok"] else "FAIL"
            print(f"- {host_name}_test_run: {host_test_status}")
            print(f"  command: {' '.join(details['command'])}")
            if details["result"]["stdout"]:
                print(f"  stdout: {details['result']['stdout']}")
            if details["result"]["stderr"]:
                print(f"  stderr: {details['result']['stderr']}")

    print(f"Recommendation: {payload['recommendation']}")

    all_probes_failed = all(
        not details["probe"]["ok"] for details in host_results.values()
    )
    if all_probes_failed:
        print("WARNING: All shell host probes failed.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

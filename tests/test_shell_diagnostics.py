import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "shell_diagnostics.py"
SPEC = importlib.util.spec_from_file_location("shell_diagnostics", MODULE_PATH)
shell_diagnostics = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(shell_diagnostics)


class ShellDiagnosticsTests(unittest.TestCase):
    def test_recommend_prefers_pwsh(self):
        results = {
            "hosts": {
                "powershell": {"probe": {"ok": False}},
                "pwsh": {"probe": {"ok": True}},
                "cmd": {"probe": {"ok": True}},
            }
        }

        recommendation = shell_diagnostics.recommend(results)

        self.assertIn("PowerShell 7", recommendation)

    def test_recommend_uses_cmd_fallback_when_only_cmd_is_healthy(self):
        results = {
            "hosts": {
                "powershell": {"probe": {"ok": False}},
                "pwsh": {"probe": {"ok": False}},
                "cmd": {"probe": {"ok": True}},
            }
        }

        recommendation = shell_diagnostics.recommend(results)

        self.assertIn("cmd.exe", recommendation)

    def test_recommend_mentions_cmd_fallback_when_powershell_is_healthy_but_cmd_exists(self):
        results = {
            "hosts": {
                "powershell": {"probe": {"ok": True}},
                "pwsh": {"probe": {"ok": False}},
                "cmd": {"probe": {"ok": True}},
            },
            "host_test_runs": {
                "powershell": {"result": {"ok": False}},
                "pwsh": {"result": {"ok": False}},
                "cmd": {"result": {"ok": True}},
            },
        }

        recommendation = shell_diagnostics.recommend(results)

        self.assertIn("cmd.exe can launch the repo tests successfully", recommendation)
        self.assertIn("cmd.exe", recommendation)

    def test_recommend_reports_runtime_issue_when_all_hosts_fail(self):
        results = {
            "hosts": {
                "powershell": {"probe": {"ok": False}},
                "pwsh": {"probe": {"ok": False}},
                "cmd": {"probe": {"ok": False}},
            },
            "host_test_runs": {
                "powershell": {"result": {"ok": False}},
                "pwsh": {"result": {"ok": False}},
                "cmd": {"result": {"ok": False}},
            },
        }

        recommendation = shell_diagnostics.recommend(results)

        self.assertIn("host/runtime issue", recommendation)

    def test_recommend_prefers_host_test_run_over_probe_only(self):
        results = {
            "hosts": {
                "powershell": {"probe": {"ok": True}},
                "pwsh": {"probe": {"ok": False}},
                "cmd": {"probe": {"ok": True}},
            },
            "host_test_runs": {
                "powershell": {"result": {"ok": True}},
                "pwsh": {"result": {"ok": False}},
                "cmd": {"result": {"ok": False}},
            },
        }

        recommendation = shell_diagnostics.recommend(results)

        self.assertIn("legacy powershell.exe is healthy", recommendation)

    def test_recommend_prefers_powershell_test_run_before_cmd_fallback(self):
        results = {
            "hosts": {
                "powershell": {"probe": {"ok": True}},
                "pwsh": {"probe": {"ok": False}},
                "cmd": {"probe": {"ok": True}},
            },
            "host_test_runs": {
                "powershell": {"result": {"ok": True}},
                "pwsh": {"result": {"ok": False}},
                "cmd": {"result": {"ok": True}},
            },
        }

        recommendation = shell_diagnostics.recommend(results)

        self.assertIn("legacy powershell.exe is healthy", recommendation)
        self.assertIn("cmd.exe", recommendation)


    def test_recommend_with_only_pwsh_probe_passing(self):
        results = {
            "hosts": {
                "powershell": {"probe": {"ok": False}},
                "pwsh": {"probe": {"ok": True}},
                "cmd": {"probe": {"ok": False}},
            },
        }
        recommendation = shell_diagnostics.recommend(results)
        self.assertIn("pwsh.exe is installed and responsive", recommendation)

    def test_recommend_without_host_test_runs_key(self):
        results = {
            "hosts": {
                "powershell": {"probe": {"ok": True}},
                "pwsh": {"probe": {"ok": False}},
                "cmd": {"probe": {"ok": False}},
            },
        }
        recommendation = shell_diagnostics.recommend(results)
        self.assertIn("powershell.exe is healthy locally", recommendation)

    def test_recommend_powershell_and_cmd_probe_fallback(self):
        results = {
            "hosts": {
                "powershell": {"probe": {"ok": True}},
                "pwsh": {"probe": {"ok": False}},
                "cmd": {"probe": {"ok": True}},
            },
        }
        recommendation = shell_diagnostics.recommend(results)
        self.assertIn("powershell.exe is healthy locally", recommendation)
        self.assertIn("cmd.exe is also available", recommendation)

    def test_run_command_returns_error_for_missing_executable(self):
        result = shell_diagnostics.run_command(["nonexistent_tool_xyz_123"])
        self.assertFalse(result["ok"])
        self.assertIn("executable not found", result["stderr"])


if __name__ == "__main__":
    unittest.main()

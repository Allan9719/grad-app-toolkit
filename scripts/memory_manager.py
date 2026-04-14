"""Command line helper for the shared candidate memory file.

The toolkit uses a repo-local JSON file to store candidate state across
different clients. This script creates the file, validates it against the
formal contract, updates nested fields safely, and keeps backups before any
mutating write.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import time
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Iterator


REPO_ROOT = Path(__file__).resolve().parents[1]
ROOT_DIR = REPO_ROOT
ASSETS_DIR = REPO_ROOT / "assets"
MEMORY_FILE = REPO_ROOT / "candidate_memory.json"
TEMPLATE_FILE = ASSETS_DIR / "memory_template.md"
CONTRACT_FILE = ASSETS_DIR / "memory_contract.json"
LEGACY_SCHEMA_FILE = ASSETS_DIR / "memory_schema.json"
DEFAULT_TEMPLATE = LEGACY_SCHEMA_FILE
DEFAULT_CONTRACT = CONTRACT_FILE
BACKUP_DIR_NAME = ".memory_backups"
BACKUP_DIR = REPO_ROOT / BACKUP_DIR_NAME
LOCK_FILE_NAME = "candidate_memory.json.lock"
LOCK_WAIT_SECONDS = 10.0
LOCK_STALE_SECONDS = 300.0


class BootstrapIssues(list):
    """Bootstrap results that stay truthy for legacy compatibility."""

    # Legacy callers checked truthiness; the CLI now uses len() instead.
    def __bool__(self) -> bool:
        return True


def load_json_file(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_json_payload(text: str) -> Any:
    stripped = text.strip()
    if not stripped:
        raise ValueError("empty template payload")

    if stripped.startswith("{") or stripped.startswith("["):
        return json.loads(stripped)

    for marker in ("```json", "```"):
        if marker in stripped:
            start = stripped.find(marker)
            body = stripped[start + len(marker):]
            end = body.rfind("```")
            if end >= 0:
                candidate = body[:end].strip()
                if candidate:
                    return json.loads(candidate)

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end > start:
        return json.loads(stripped[start:end + 1])

    start = stripped.find("[")
    end = stripped.rfind("]")
    if start >= 0 and end > start:
        return json.loads(stripped[start:end + 1])

    raise ValueError("could not locate JSON payload in template")


def load_schema_contract() -> dict[str, Any]:
    schema_path = DEFAULT_CONTRACT
    if not schema_path.exists():
        raise FileNotFoundError(
            "memory contract is missing; expected assets/memory_contract.json"
        )
    schema = load_json_file(schema_path)
    if not isinstance(schema, dict):
        raise ValueError("memory contract must be a JSON object")
    return schema


def build_default_from_schema(schema: dict[str, Any]) -> Any:
    schema_type = schema.get("type")
    types = schema_type if isinstance(schema_type, list) else [schema_type]
    types = [item for item in types if item]

    if "const" in schema:
        return deepcopy(schema["const"])
    if schema.get("enum"):
        return deepcopy(schema["enum"][0])
    if "default" in schema:
        return deepcopy(schema["default"])
    if "null" in types:
        return None
    if "object" in types:
        result: dict[str, Any] = {}
        for key, value in schema.get("properties", {}).items():
            result[key] = build_default_from_schema(value)
        return result
    if "array" in types:
        return []
    if "boolean" in types:
        return False
    if "integer" in types:
        if isinstance(schema.get("minimum"), (int, float)):
            return int(schema["minimum"])
        return 0
    if "number" in types:
        if isinstance(schema.get("minimum"), (int, float)):
            return schema["minimum"]
        return 0
    if "string" in types:
        if isinstance(schema.get("minLength"), int) and schema["minLength"] > 0:
            return "placeholder"
        return ""
    return None


def load_template_state(template_path: Path | None = None) -> dict[str, Any]:
    candidates = (
        [Path(template_path)]
        if template_path
        else [DEFAULT_TEMPLATE, TEMPLATE_FILE]
    )
    for candidate in candidates:
        if candidate.exists():
            try:
                payload = extract_json_payload(candidate.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    return payload
            except Exception:
                continue

    return build_default_from_schema(load_schema_contract())


def memory_lock_path() -> Path:
    return MEMORY_FILE.with_name(LOCK_FILE_NAME)


def is_stale_lock(lock_path: Path, stale_after_seconds: float = LOCK_STALE_SECONDS) -> bool:
    try:
        return (time.time() - lock_path.stat().st_mtime) > stale_after_seconds
    except FileNotFoundError:
        return False


@contextmanager
def memory_lock() -> Iterator[None]:
    lock_path = memory_lock_path()
    deadline = time.time() + LOCK_WAIT_SECONDS

    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if is_stale_lock(lock_path):
                try:
                    lock_path.unlink()
                except FileNotFoundError:
                    pass
                continue
            if time.time() >= deadline:
                raise TimeoutError(
                    f"Timed out waiting for memory lock: {lock_path}"
                )
            time.sleep(0.1)
            continue

        try:
            os.write(
                fd,
                json.dumps(
                    {"pid": os.getpid(), "created_at": datetime.now().isoformat()}
                ).encode("utf-8"),
            )
        finally:
            os.close(fd)
        break

    try:
        yield
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", delete=False, dir=path.parent, prefix=path.name + ".", suffix=".tmp"
        ) as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            temp_name = handle.name
        os.replace(temp_name, path)
    except BaseException:
        if temp_name is not None:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
        raise


def format_memory_path(segments: Iterable[str]) -> str:
    return " -> ".join(segment for segment in segments if segment)


def parse_memory_path(path_expression: str | Iterable[str]) -> list[str]:
    if isinstance(path_expression, str):
        segments = [segment.strip() for segment in path_expression.split("->")]
    else:
        segments = [str(segment).strip() for segment in path_expression]
    return [segment for segment in segments if segment]


def expected_type_description(schema: dict[str, Any]) -> str:
    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        non_null = [item for item in schema_type if item != "null"]
        if not non_null:
            return "null"
        if len(non_null) == 1:
            return f"{non_null[0]} or null"
        return ", ".join(non_null[:-1]) + f" or {non_null[-1]}"
    if isinstance(schema_type, str):
        return schema_type
    if schema.get("enum"):
        return "one of " + ", ".join(repr(value) for value in schema["enum"])
    return "a valid value"


def get_schema_node(schema: dict[str, Any], path_segments: list[str]) -> dict[str, Any] | None:
    node = schema
    for segment in path_segments:
        node_type = node.get("type")
        node_types = node_type if isinstance(node_type, list) else [node_type]

        if "object" in node_types or node.get("properties"):
            properties = node.get("properties", {})
            if segment not in properties:
                return None
            node = properties[segment]
            continue

        if "array" in node_types:
            items = node.get("items")
            if not isinstance(items, dict):
                return None
            if not segment.isdigit():
                return None
            node = items
            continue

        return None

    return node


def get_value_at_path(state: Any, path_segments: list[str]) -> Any:
    current = state
    for segment in path_segments:
        if isinstance(current, list):
            index = int(segment)
            current = current[index]
        else:
            current = current[segment]
    return current


def set_value_at_path(state: dict[str, Any], path_segments: list[str], value: Any) -> None:
    current: Any = state
    for segment in path_segments[:-1]:
        if isinstance(current, list):
            current = current[int(segment)]
        else:
            current = current[segment]

    last_segment = path_segments[-1]
    if isinstance(current, list):
        current[int(last_segment)] = value
    else:
        current[last_segment] = value


def validate_value_against_schema(value: Any, schema: dict[str, Any], path: str = "value") -> list[str]:
    issues: list[str] = []
    schema_type = schema.get("type")
    types = schema_type if isinstance(schema_type, list) else [schema_type]
    types = [item for item in types if item]

    if value is None:
        if "null" in types or not types:
            pass
        else:
            issues.append(f"{path}: invalid type, expected {expected_type_description(schema)}")
            return issues
    elif "object" in types:
        if not isinstance(value, dict):
            issues.append(f"{path}: invalid type, expected {expected_type_description(schema)}")
            return issues
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        for required_key in required:
            if required_key not in value:
                issues.append(f"{path}: missing required key '{required_key}'")
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    issues.append(f"{path}: unexpected key '{key}'")
        for key, subschema in properties.items():
            if key in value:
                issues.extend(
                    validate_value_against_schema(value[key], subschema, f"{path} -> {key}")
                )
    elif "array" in types:
        if not isinstance(value, list):
            issues.append(f"{path}: invalid type, expected {expected_type_description(schema)}")
            return issues
        items = schema.get("items")
        if isinstance(items, dict):
            for index, item in enumerate(value):
                issues.extend(
                    validate_value_against_schema(item, items, f"{path}[{index}]")
                )
    elif "string" in types:
        if not isinstance(value, str):
            issues.append(f"{path}: invalid type, expected {expected_type_description(schema)}")
            return issues
        if isinstance(schema.get("minLength"), int) and len(value) < schema["minLength"]:
            issues.append(f"{path}: length must be >= {schema['minLength']}")
        if isinstance(schema.get("maxLength"), int) and len(value) > schema["maxLength"]:
            issues.append(f"{path}: length must be <= {schema['maxLength']}")
    elif "boolean" in types:
        if not isinstance(value, bool):
            issues.append(f"{path}: invalid type, expected {expected_type_description(schema)}")
            return issues
    elif "integer" in types:
        if not isinstance(value, int) or isinstance(value, bool):
            issues.append(f"{path}: invalid type, expected {expected_type_description(schema)}")
            return issues
    elif "number" in types:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            issues.append(f"{path}: invalid type, expected {expected_type_description(schema)}")
            return issues
    elif "null" in types:
        if value is not None:
            issues.append(f"{path}: invalid type, expected null")
            return issues

    if "enum" in schema and value not in schema["enum"]:
        issues.append(
            f"{path}: invalid value, expected one of {', '.join(repr(item) for item in schema['enum'])}"
        )

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            issues.append(f"{path}: value must be >= {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            issues.append(f"{path}: value must be <= {schema['maximum']}")

    return issues


def validate_state(state: dict[str, Any] | None = None) -> list[str]:
    if state is None:
        if not MEMORY_FILE.exists():
            return [
                "memory file missing; run 'python scripts/memory_manager.py bootstrap' first"
            ]
        try:
            state = load_json_file(MEMORY_FILE)
        except Exception:
            return [
                "memory file unreadable; restore from backup or re-bootstrap"
            ]

    try:
        contract = load_schema_contract()
    except Exception as exc:
        return [f"memory contract unreadable: {exc}"]

    return validate_value_against_schema(state, contract, "memory")


def read_state(show_missing_hint: bool = True) -> dict[str, Any] | None:
    if not MEMORY_FILE.exists():
        if show_missing_hint:
            print("Memory file not found. Run bootstrap or init first.", file=sys.stderr)
        return None

    try:
        payload = load_json_file(MEMORY_FILE)
    except Exception:
        if show_missing_hint:
            print("Memory file unreadable. Restore from backup or bootstrap.", file=sys.stderr)
        return None

    if not isinstance(payload, dict):
        if show_missing_hint:
            print("Memory file unreadable. Restore from backup or bootstrap.", file=sys.stderr)
        return None

    return payload


def create_backup() -> Path:
    if not MEMORY_FILE.exists():
        raise FileNotFoundError("memory file is missing")

    backup_dir = BACKUP_DIR
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"memory_backup_{timestamp}.json"
    counter = 1
    while backup_path.exists():
        backup_path = backup_dir / f"memory_backup_{timestamp}_{counter}.json"
        counter += 1
    shutil.copy2(MEMORY_FILE, backup_path)
    print(f"Backup saved to: {backup_path}")
    return backup_path


def _initialize_memory_unlocked(template_path: Path | None = None) -> Path:
    if MEMORY_FILE.exists():
        print(f"Memory file already exists at: {MEMORY_FILE}")
        return MEMORY_FILE

    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    state = load_template_state(template_path)
    write_json_atomic(MEMORY_FILE, state)
    print(f"Created {MEMORY_FILE} from template.")
    return MEMORY_FILE


def initialize_memory(template_path: Path | None = None) -> Path:
    print("Initiating Memory Manager...")
    with memory_lock():
        return _initialize_memory_unlocked(template_path)


def bootstrap_memory(template_path: Path | None = None) -> BootstrapIssues:
    print("Initiating Memory Manager...")
    with memory_lock():
        if not MEMORY_FILE.exists():
            _initialize_memory_unlocked(template_path)
        state = read_state(show_missing_hint=False)
        issues = (
            validate_state(state)
            if state is not None
            else ["memory file unreadable; restore from backup or re-bootstrap"]
        )

    if issues:
        print("Memory bootstrap failed:", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return BootstrapIssues(issues)

    print("Memory file bootstrapped and validated.")
    return BootstrapIssues()


def _update_field_unlocked(path_expression: str | Iterable[str], value: Any) -> bool:
    state = read_state(show_missing_hint=False)
    if state is None:
        print("Error: Memory file not found. Run bootstrap or init first.", file=sys.stderr)
        return False

    path_segments = parse_memory_path(path_expression)
    if not path_segments:
        print("Error: path is required", file=sys.stderr)
        return False

    try:
        contract = load_schema_contract()
    except Exception as exc:
        print(f"Error: memory contract unreadable: {exc}", file=sys.stderr)
        return False

    schema_node = get_schema_node(contract, path_segments)
    if schema_node is None:
        print(f"Error: Unknown memory path {format_memory_path(path_segments)}", file=sys.stderr)
        return False

    issues = validate_value_against_schema(value, schema_node, "value")
    if issues:
        print(f"Error: {issues[0]}", file=sys.stderr)
        return False

    try:
        create_backup()
    except FileNotFoundError:
        print("Error: Memory file not found. Run bootstrap or init first.", file=sys.stderr)
        return False

    state = deepcopy(state)
    set_value_at_path(state, path_segments, value)
    write_json_atomic(MEMORY_FILE, state)
    print(f"Successfully updated {format_memory_path(path_segments)}")
    return True


def update_field(path_expression: str | Iterable[str], value: Any) -> bool:
    with memory_lock():
        return _update_field_unlocked(path_expression, value)


def coerce_cli_value(raw_value: str) -> Any:
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return raw_value


def print_state(state: dict[str, Any]) -> None:
    print(json.dumps(state, indent=2, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="memory_manager.py",
        description="Manage the grad-app-toolkit candidate memory file.",
    )
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init", help="Create candidate_memory.json from the template.")
    init_parser.add_argument("--template", type=Path, default=None, help="Optional template file path.")

    subparsers.add_parser("read", help="Print the current memory file.")
    subparsers.add_parser("validate", help="Validate candidate_memory.json against the contract.")

    update_parser = subparsers.add_parser("update", help="Update a nested memory field.")
    update_parser.add_argument("path", help="Arrow-separated path, e.g. static_profile -> metrics -> gpa")
    update_parser.add_argument("value", help="New value. JSON is accepted when possible.")

    bootstrap_parser = subparsers.add_parser(
        "bootstrap",
        help="Create candidate_memory.json if missing and validate it immediately.",
    )
    bootstrap_parser.add_argument("--template", type=Path, default=None, help="Optional template file path.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 1

    if args.command == "init":
        initialize_memory(args.template)
        return 0

    if args.command == "read":
        state = read_state()
        if state is None:
            return 1
        print_state(state)
        return 0

    if args.command == "validate":
        issues = validate_state()
        if issues:
            print("Memory validation failed:", file=sys.stderr)
            for issue in issues:
                print(f"- {issue}", file=sys.stderr)
            return 1
        print("Memory file matches contract.")
        return 0

    if args.command == "update":
        if update_field(args.path, coerce_cli_value(args.value)):
            return 0
        return 1

    if args.command == "bootstrap":
        issues = bootstrap_memory(args.template)
        return 0 if len(issues) == 0 else 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

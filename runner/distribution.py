"""Install and verify the Book Genesis skill bundle for native agent hosts.

Nothing here calls a model or writes a book. The installer copies skill folders
(and, for Claude Code, generated subagent files), records digests, and checks
them later.
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
from typing import Mapping
from uuid import uuid4

from runner.agents import AGENTS_RELATIVE, AGENT_SPECS, agent_drift
from runner.filesystem import REPO_ROOT, load_manifest


DISTRIBUTION_MANIFEST_PATH = REPO_ROOT / "distribution" / "portable-suite.json"
MANIFEST_SCHEMA = 2
RECORD_SCHEMA = 2
INSTALL_RECORD = ".book-genesis-install.json"
BACKUP_DIRECTORY = ".book-genesis-backups"
BACKUP_SUFFIX = ".bak"
REQUIRED_PHASES = ("Phase 4: Adversarial Audit", "Phase 5: Revision Loop")
REQUIRED_CORE_FILES = (
    "references/pipeline/host-contract.md",
    "references/pipeline/project-state.yaml",
    "references/scoring/evaluator-protocol.md",
)
SCANNED_SUFFIXES = {".md", ".yaml", ".yml", ".json"}
REFERENCE_PATTERN = re.compile(r"(?<![\w./-])references/[\w./-]*?[\w-]\.(?:md|yaml|yml|json)(?![\w-])(?!\.\w)")
OUTSIDE_PATTERNS = (
    re.compile(r"(?<![\w-])skills/[a-z0-9-]+/"),
    re.compile(r"(?<![\w-])knowledge/[\w.-]+\.md"),
    re.compile(r"~/Desktop"),
    re.compile(r"(?<![\w./-])runner/cli\.py"),
    re.compile(r"(?<![\w.])\.\./"),
)


# ---------------------------------------------------------------- manifest


def load_distribution_manifest(path: Path = DISTRIBUTION_MANIFEST_PATH) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != MANIFEST_SCHEMA:
        raise ValueError(f"Unsupported portable suite manifest version in {path}")
    return data


def supported_targets() -> tuple[str, ...]:
    targets = load_distribution_manifest().get("targets", {})
    if not isinstance(targets, dict):
        raise ValueError("Portable suite targets must be an object")
    return tuple(sorted(str(name) for name in targets))


def selected_skills() -> list[str]:
    return [str(name) for name in load_distribution_manifest().get("skills", [])]


def _retired() -> dict[str, list[str]]:
    retired = load_distribution_manifest().get("retired", {})
    if not isinstance(retired, dict):
        return {"skills": [], "claude_files": []}
    return {
        "skills": [str(name) for name in retired.get("skills", [])],
        "claude_files": [str(name) for name in retired.get("claude_files", [])],
    }


def _target_spec(target: str) -> dict[str, object]:
    targets = load_distribution_manifest().get("targets", {})
    if not isinstance(targets, dict) or target not in targets:
        available = ", ".join(supported_targets())
        raise KeyError(f"Unknown install target {target!r}. Available targets: {available}")
    spec = targets[target]
    if not isinstance(spec, dict):
        raise ValueError(f"Invalid install target definition for {target}")
    return spec


# ------------------------------------------------------------------ paths


def _absolute_from_environment(name: str, value: str) -> Path:
    path = Path(value).expanduser()
    if not path.anchor:
        raise ValueError(f"{name} must be an absolute path, got {value!r}")
    return path


def _runtime_home(
    spec: Mapping[str, object],
    home: Path | None,
    environ: Mapping[str, str] | None,
) -> Path:
    environment = os.environ if environ is None else environ
    home_env = str(spec.get("home_env", ""))
    configured = environment.get(home_env, "").strip() if home_env else ""
    if configured:
        return _absolute_from_environment(home_env, configured) / str(spec.get("configured_home_subdir", ""))
    xdg_home = environment.get("XDG_CONFIG_HOME", "").strip()
    if xdg_home and spec.get("xdg_config_subdir"):
        return _absolute_from_environment("XDG_CONFIG_HOME", xdg_home) / str(spec["xdg_config_subdir"])
    return (home or Path.home()) / str(spec["default_home"])


def resolve_install_root(
    target: str,
    *,
    destination: str | Path | None = None,
    home: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> Path:
    spec = _target_spec(target)
    if destination is not None:
        return Path(destination).expanduser().resolve()
    return (_runtime_home(spec, home, environ) / str(spec["skills_dir"])).resolve()


def resolve_agents_root(
    target: str,
    *,
    destination: str | Path | None = None,
    agents_destination: str | Path | None = None,
    home: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> tuple[Path | None, str]:
    """Where Claude Code subagents go, or (None, reason) when they are skipped."""
    agents = load_distribution_manifest().get("claude_agents", {})
    if not isinstance(agents, dict) or target not in agents.get("targets", []):
        return None, ""
    if agents_destination is not None:
        return Path(agents_destination).expanduser().resolve(), ""
    if destination is not None:
        return None, "Claude Code subagents were not installed; add --agents-dest to install them next to a custom --dest"
    home_dir = _runtime_home(_target_spec(target), home, environ)
    return (home_dir / str(agents.get("install_subdir", "agents"))).resolve(), ""


# --------------------------------------------------------------- checking


def read_frontmatter(path: Path) -> dict[str, str]:
    """Read the flat frontmatter of a SKILL.md, refusing what YAML hosts would reject."""
    text = path.read_text(encoding="utf-8")
    if text.startswith("\ufeff"):
        text = text[1:]
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path.as_posix()}: frontmatter must open with ---")
    values: dict[str, str] = {}
    current = ""
    for line in lines[1:]:
        if line.strip() == "---":
            return values
        if not line.strip():
            continue
        if line[:1] in (" ", "\t"):
            if current:
                values[current] = (values[current] + " " + line.strip()).strip()
            continue
        current = ""
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if value in {"", "|", ">", "|-", ">-", "|+", ">+"}:
            values[key] = ""
            current = key
        elif value[:1] in {'"', "'"}:
            values[key] = value[1:-1] if len(value) >= 2 and value[-1] == value[0] else value
        else:
            if ": " in value or " #" in value:
                raise ValueError(
                    f"{path.as_posix()}: quote the value of {key}; unquoted ': ' or ' #' breaks YAML hosts"
                )
            values[key] = value
            current = key
    raise ValueError(f"{path.as_posix()}: frontmatter is not closed")


def find_skill_problems(skill_root: Path, *, retired_names: list[str]) -> list[str]:
    """Report anything that would break once this folder is installed on its own."""
    retired_patterns = [
        (name, re.compile(rf"(?:`|\$|/){re.escape(name)}(?![\w-])(?!\.[a-z])"))
        for name in retired_names
    ]
    problems: list[str] = []
    for path in sorted(item for item in skill_root.rglob("*") if item.is_file()):
        if path.suffix.lower() not in SCANNED_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8")
        label = f"{skill_root.name}/{path.relative_to(skill_root).as_posix()}"
        seen: set[str] = set()
        for match in REFERENCE_PATTERN.finditer(text):
            reference = match.group(0)
            if reference in seen:
                continue
            seen.add(reference)
            if not (skill_root / reference).is_file():
                problems.append(f"{label}: missing file {reference}")
        for name, pattern in retired_patterns:
            if pattern.search(text):
                problems.append(f"{label}: names retired skill {name}")
        for pattern in OUTSIDE_PATTERNS:
            found: list[str] = []
            for match in pattern.finditer(text):
                if match.group(0) not in found:
                    found.append(match.group(0))
            problems.extend(f"{label}: path outside the skill: {item}" for item in found)
    return problems


def validate_suite() -> dict[str, object]:
    manifest = load_distribution_manifest()
    errors: list[str] = []
    skills = selected_skills()
    retired = _retired()
    canonical = str(manifest.get("canonical_skill", ""))

    if canonical not in skills:
        errors.append(f"canonical skill {canonical!r} is not in the skill list")
    if len(skills) != len(set(skills)):
        errors.append("skill list contains duplicates")
    for name in sorted(set(skills) & set(retired["skills"])):
        errors.append(f"skill is both shipped and retired: {name}")

    for name in skills:
        skill_root = REPO_ROOT / "skills" / name
        skill_file = skill_root / "SKILL.md"
        if not skill_file.is_file():
            errors.append(f"missing skill entrypoint: skills/{name}/SKILL.md")
            continue
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
            errors.append(f"invalid skill name: {name}")
        try:
            frontmatter = read_frontmatter(skill_file)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if frontmatter.get("name") != name:
            errors.append(f"skill name mismatch in skills/{name}/SKILL.md")
        if not 1 <= len(frontmatter.get("description", "")) <= 1024:
            errors.append(f"skill description must be 1-1024 characters: {name}")
        errors.extend(find_skill_problems(skill_root, retired_names=retired["skills"]))

    core = REPO_ROOT / "skills" / canonical
    for relative in REQUIRED_CORE_FILES:
        if not (core / relative).is_file():
            errors.append(f"core reference missing: {relative}")
    manifest_path = core / "references" / "pipeline" / "manifest.yaml"
    if manifest_path.is_file():
        errors.extend(_pipeline_problems(core, manifest_path))
    else:
        errors.append("core pipeline manifest missing: references/pipeline/manifest.yaml")

    errors.extend(agent_drift(REPO_ROOT))
    return {"ok": not errors, "errors": errors, "warnings": []}


def _pipeline_problems(core: Path, manifest_path: Path) -> list[str]:
    problems: list[str] = []
    phases = load_manifest(manifest_path)
    labels = [phase.label for phase in phases]
    if len(set(labels)) != len(labels):
        problems.append("pipeline contains duplicate phase labels")
    gates = [phase.gate for phase in phases]
    if len(set(gates)) != len(gates):
        problems.append("pipeline contains duplicate gates")
    for required in REQUIRED_PHASES:
        if required not in labels:
            problems.append(f"pipeline is missing mandatory phase: {required}")
    for index, phase in enumerate(phases):
        expected_next = phases[index + 1].label if index + 1 < len(phases) else ""
        if phase.next != expected_next:
            problems.append(f"pipeline order broken at {phase.label}")
        if not (core / phase.prompt).is_file():
            problems.append(f"phase prompt missing: {phase.prompt}")
        for reference in phase.references:
            if not (core / reference).is_file():
                problems.append(f"phase reference missing: {reference}")
    return problems


# -------------------------------------------------------------- verifying


def _read_record(root: Path) -> tuple[dict[str, object] | None, str]:
    """Return (record, problem). A 5.x record is returned with its problem noted."""
    path = root / INSTALL_RECORD
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, "no install record; this directory was not installed by this installer"
    except ValueError as exc:
        return None, f"install record is not valid JSON: {exc}"
    if not isinstance(data, dict) or not isinstance(data.get("skills"), dict):
        return None, "install record is invalid"
    for section in ("agents", "legacy_claude_files"):
        if section in data and not isinstance(data[section], dict):
            return None, "install record is invalid"
    if data.get("schema_version") == 1:
        return data, "install record is from Book Genesis 5.x; run install to upgrade"
    if data.get("schema_version") != RECORD_SCHEMA:
        return None, "install record has an unknown schema version"
    return data, ""


def _recorded(record: dict[str, object] | None, section: str) -> dict[str, str]:
    values = record.get(section, {}) if record else {}
    return {str(key): str(value) for key, value in values.items()} if isinstance(values, dict) else {}


def verify_install(
    target: str,
    *,
    destination: str | Path | None = None,
    home: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Compare installed files with their record and this checkout; never run a host or model."""
    root = resolve_install_root(target, destination=destination, home=home, environ=environ)
    errors: list[str] = []
    record, record_problem = _read_record(root)
    if record_problem:
        errors.append(record_problem)
    current = record if record is not None and record.get("schema_version") == RECORD_SCHEMA else None
    recorded_skills = _recorded(current, "skills")

    for name in selected_skills():
        installed = root / name
        if not (installed / "SKILL.md").is_file():
            errors.append(f"missing skill: {name}")
            continue
        digest = _tree_digest(installed)
        if digest == _tree_digest(REPO_ROOT / "skills" / name):
            if current is not None and recorded_skills.get(name) != digest:
                errors.append(f"install record mismatch: {name}")
        elif current is not None and recorded_skills.get(name) == digest:
            errors.append(f"installed copy of {name} is from another version of this checkout; run install to update it")
        else:
            errors.append(f"{name} was changed after it was installed; compare it with this checkout before reinstalling")

    if current is not None:
        agents_root = Path(str(current.get("agents_root", "")))
        for name, recorded in _recorded(current, "agents").items():
            installed = agents_root / name
            if not installed.is_file():
                errors.append(f"missing agent: {installed}")
            elif _file_digest(installed) != recorded:
                errors.append(f"changed agent: {installed}")
            elif recorded != _file_digest(REPO_ROOT / AGENTS_RELATIVE / name):
                errors.append(f"agent {name} is from another version of this checkout; run install to update it")
    return {"ok": not errors, "destination": str(root), "errors": errors}


# ------------------------------------------------------------- installing


def _is_link(path: Path) -> bool:
    """True for symlinks and Windows junctions, which the installer never follows."""
    if path.is_symlink():
        return True
    isjunction = getattr(os.path, "isjunction", None)
    if isjunction is not None and isjunction(path):
        return True
    try:
        attributes = getattr(os.lstat(path), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attributes & 0x400)  # FILE_ATTRIBUTE_REPARSE_POINT


def _plan(source_digest: str, destination: Path, digest_of, force: bool, recorded: str) -> str:
    """install | unchanged | update | replace | conflict | link"""
    if _is_link(destination):
        return "link"
    if not destination.exists():
        return "install"
    current = digest_of(destination)
    if current == source_digest:
        return "unchanged"
    if recorded and current == recorded:
        return "update"
    return "replace" if force else "conflict"


def _plan_retirements(target: str, destination_root: Path) -> tuple[list[dict[str, str]], list[str]]:
    """Retire what an earlier Book Genesis installer put here and nobody changed since."""
    retired = _retired()
    record, _ = _read_record(destination_root)
    recorded_skills = _recorded(record, "skills")
    recorded_files = _recorded(record, "legacy_claude_files")
    retirements: list[dict[str, str]] = []
    warnings: list[str] = []

    candidates = [("skill", name, destination_root / name, _tree_digest, recorded_skills.get(name, ""))
                  for name in retired["skills"]]
    if target == "claude":
        candidates += [("file", relative, destination_root.parent / relative, _file_digest, recorded_files.get(relative, ""))
                       for relative in retired["claude_files"]]
    for kind, name, path, digest_of, recorded in candidates:
        if not (path.exists() or _is_link(path)):
            continue
        if _is_link(path):
            warnings.append(f"{path} is a link to an earlier Book Genesis {kind}; left in place, remove it yourself")
        elif recorded and recorded == digest_of(path):
            retirements.append({"kind": kind, "name": name, "path": str(path)})
        elif kind == "skill":
            warnings.append(
                f"{path} looks like a skill from an earlier Book Genesis but was changed or not "
                "installed by this installer, so it was left in place; it can compete with book-genesis"
            )
        else:
            warnings.append(
                f"{path} looks like a Book Genesis V4 file but was changed or not installed by this "
                "installer, so it was left in place; old agents can take over book requests"
            )
    return retirements, warnings


def _result(ok: bool, destination: Path | str, *, errors: list[str], dry_run: bool = False, **plan: object) -> dict[str, object]:
    result: dict[str, object] = {
        "ok": ok,
        "destination": str(destination),
        "dry_run": dry_run,
        "agents_root": "",
        "actions": [],
        "agent_actions": [],
        "retirements": [],
        "warnings": [],
        "notes": [],
        "conflicts": [],
        "backups": [],
        "errors": errors,
    }
    result.update(plan)
    return result


def install_suite(
    target: str,
    *,
    destination: str | Path | None = None,
    agents_destination: str | Path | None = None,
    force: bool = False,
    dry_run: bool = False,
    home: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, object]:
    validation = validate_suite()
    if not validation["ok"]:
        return _result(False, "", errors=list(validation["errors"]), dry_run=dry_run)  # type: ignore[arg-type]

    destination_root = resolve_install_root(target, destination=destination, home=home, environ=environ)
    source_root = (REPO_ROOT / "skills").resolve()
    if (
        destination_root == source_root
        or destination_root.is_relative_to(source_root)
        or source_root.is_relative_to(destination_root)
    ):
        return _result(False, destination_root, dry_run=dry_run,
                       errors=["installation destination cannot overlap repository source skills directory"])
    if _is_link(destination_root):
        return _result(False, destination_root, dry_run=dry_run,
                       errors=[f"{destination_root} is a link; install into the real folder instead"])
    if destination_root.exists() and not destination_root.is_dir():
        return _result(False, destination_root, dry_run=dry_run,
                       errors=["installation destination exists and is not a directory"])

    agents_root, agents_note = resolve_agents_root(
        target, destination=destination, agents_destination=agents_destination, home=home, environ=environ
    )
    notes = [agents_note] if agents_note else []
    if agents_destination is not None and agents_root is None:
        notes.append(f"--agents-dest is only used for claude; ignored for {target}")

    record, _ = _read_record(destination_root)
    recorded_skills = _recorded(record, "skills")
    recorded_agents = _recorded(record, "agents")

    actions: list[dict[str, str]] = []
    for name in selected_skills():
        action = _plan(_tree_digest(source_root / name), destination_root / name, _tree_digest, force,
                       recorded_skills.get(name, ""))
        actions.append({"skill": name, "action": action, "destination": str(destination_root / name)})

    agent_actions: list[dict[str, str]] = []
    if agents_root is not None:
        for spec in AGENT_SPECS:
            installed = agents_root / spec.agent_file
            action = _plan(_file_digest(REPO_ROOT / AGENTS_RELATIVE / spec.agent_file), installed, _file_digest,
                           force, recorded_agents.get(spec.agent_file, ""))
            agent_actions.append({"agent": spec.agent_file, "action": action, "destination": str(installed)})

    retirements, warnings = _plan_retirements(target, destination_root)
    conflicts = [item["skill"] for item in actions if item["action"] == "conflict"]
    conflicts += [f"agents/{item['agent']}" for item in agent_actions if item["action"] == "conflict"]
    links = [item["destination"] for item in actions + agent_actions if item["action"] == "link"]
    plan = {"agents_root": str(agents_root or ""), "actions": actions, "agent_actions": agent_actions,
            "retirements": retirements, "warnings": warnings, "notes": notes, "conflicts": conflicts}

    errors = [f"{path} is a link; the installer never replaces links, move it aside yourself" for path in links]
    if conflicts:
        errors.append("installed files differ from this checkout; rerun with --force to back them up and replace them")
    if errors:
        return _result(False, destination_root, errors=errors, dry_run=dry_run, **plan)
    if dry_run:
        return _result(True, destination_root, errors=[], dry_run=True, **plan)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    groups = [(destination_root,
               {item["skill"]: source_root / item["skill"] for item in actions if item["action"] != "unchanged"},
               destination_root / BACKUP_DIRECTORY / timestamp, shutil.copytree)]
    if agents_root is not None:
        groups.append((agents_root,
                       {item["agent"]: REPO_ROOT / AGENTS_RELATIVE / item["agent"]
                        for item in agent_actions if item["action"] != "unchanged"},
                       agents_root / BACKUP_DIRECTORY / timestamp, shutil.copy2))
    used_backups = _swap_groups(groups)

    retire_backup = destination_root / BACKUP_DIRECTORY / timestamp / "retired"
    for item in retirements:
        try:
            _move_to_backup(Path(item["path"]), retire_backup / item["name"])
            used_backups.add(destination_root / BACKUP_DIRECTORY / timestamp)
        except OSError as exc:
            warnings.append(f"could not move {item['path']} aside ({exc}); it is still in place")
            item["kind"] = "failed"
    plan["retirements"] = [item for item in retirements if item["kind"] != "failed"]

    new_record = {
        "schema_version": RECORD_SCHEMA,
        "suite": load_distribution_manifest()["suite_name"],
        "target": target,
        "canonical_skill": load_distribution_manifest()["canonical_skill"],
        "installed_at_utc": datetime.now(timezone.utc).isoformat(),
        "skills": {item["skill"]: _tree_digest(destination_root / item["skill"]) for item in actions},
        "agents_root": str(agents_root or ""),
        "agents": {item["agent"]: _file_digest(Path(item["destination"])) for item in agent_actions},
    }
    (destination_root / INSTALL_RECORD).write_text(json.dumps(new_record, indent=2) + "\n", encoding="utf-8")
    return _result(True, destination_root, errors=[], backups=[str(path) for path in sorted(used_backups)], **plan)


def _swap_groups(groups: list[tuple[Path, dict[str, Path], Path, object]]) -> set[Path]:
    """Stage every group first, then swap them all; any failure restores every swap made so far."""
    stages: list[Path] = []
    swapped: list[tuple[Path, Path | None, Path | None]] = []
    used: set[Path] = set()
    try:
        for parent, sources, _, copy in groups:
            if not sources:
                stages.append(Path())
                continue
            parent.mkdir(parents=True, exist_ok=True)
            stage = parent / f".book-genesis-stage-{uuid4().hex}"
            stages.append(stage)
            stage.mkdir()
            for name, source in sources.items():
                copy(source, stage / name)  # type: ignore[operator]
        try:
            for (parent, sources, backup_root, _), stage in zip(groups, stages):
                for name in sources:
                    target = parent / name
                    backup = disabled = None
                    if target.exists():
                        backup = backup_root / name
                        disabled = _move_to_backup(target, backup)
                        used.add(backup_root)
                    swapped.append((target, backup, disabled))
                    (stage / name).rename(target)
        except Exception:
            for target, backup, disabled in reversed(swapped):
                _remove(target)
                if backup is not None:
                    _restore_backup(backup, target, disabled)
            raise
    finally:
        for stage in stages:
            if stage != Path():
                shutil.rmtree(stage, ignore_errors=True)
    return used


def _free_name(path: Path) -> Path:
    if not path.exists():
        return path
    index = 1
    while path.with_name(f"{path.name}.{index}").exists():
        index += 1
    return path.with_name(f"{path.name}.{index}")


def _move_to_backup(path: Path, backup: Path) -> Path | None:
    """Move aside so no host loads it; SKILL.md and agent files get a .bak name.

    Returns the disabled file's new path. If anything fails, the item is put
    back where it was before the error is raised.
    """
    if _is_link(path):
        raise OSError(f"{path} is a link; the installer never moves links")
    if backup.exists():
        raise FileExistsError(f"backup already exists: {backup}")
    backup.parent.mkdir(parents=True, exist_ok=True)
    path.rename(backup)
    try:
        if backup.is_dir():
            skill_file = backup / "SKILL.md"
            if not skill_file.exists():
                return None
            disabled = _free_name(backup / ("SKILL.md" + BACKUP_SUFFIX))
            skill_file.rename(disabled)
            return disabled
        disabled = _free_name(backup.with_name(backup.name + BACKUP_SUFFIX))
        backup.rename(disabled)
        return disabled
    except Exception:
        if backup.exists():
            backup.rename(path)
        raise


def _restore_backup(backup: Path, target: Path, disabled: Path | None) -> None:
    if backup.is_dir():
        if disabled is not None and disabled.exists():
            disabled.rename(backup / "SKILL.md")
        backup.rename(target)
    elif disabled is not None and disabled.exists():
        disabled.rename(target)


def _remove(path: Path) -> None:
    if _is_link(path):
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def _file_digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest() if path.is_file() else ""


def _tree_digest(root: Path) -> str:
    digest = sha256()
    if not root.is_dir():
        return ""
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        content = path.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()

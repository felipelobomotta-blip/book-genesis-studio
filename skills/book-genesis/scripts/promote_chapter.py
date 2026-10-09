"""Safely promote a panel-approved chapter revision.

The writer never calls this helper with a score.  The caller supplies a frozen
decision record containing four complete reader votes and the hashes of the
accepted and staged files.  The helper verifies that record, snapshots the
accepted file, and performs one atomic insertion when the host supports it.
The fallback is guarded by a cooperative single-writer lock.  Any failed
check leaves the accepted chapter in place or preserves a detected concurrent
version for reconciliation.

This module intentionally uses only the Python standard library.  It is a
small workflow guard, not a quality evaluator or a network client.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping


class PromotionError(ValueError):
    """Raised when a chapter cannot be promoted safely."""


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REQUIRED_VOTE_FIELDS = {"reader", "prefers", "turn_page"}


class _ExclusiveLock:
    """A small cooperative single-writer lock for one book checkout."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._fd: int | None = None

    def __enter__(self) -> "_ExclusiveLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._fd = os.open(
                self.path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            )
            os.write(self._fd, f"pid={os.getpid()}\n".encode("ascii"))
        except FileExistsError as exc:
            raise PromotionError(f"book write lock is already held: {self.path}") from exc
        except OSError:
            if self._fd is not None:
                os.close(self._fd)
                self._fd = None
            self.path.unlink(missing_ok=True)
            raise
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> bool:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        self.path.unlink(missing_ok=True)
        return False


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of *path* without loading it all at once."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PromotionError(f"decision contains duplicate key {key!r}")
        result[key] = value
    return result


def _read_decision(path: Path) -> tuple[dict[str, Any], str]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise PromotionError(f"cannot read decision JSON: {exc}") from exc
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError, PromotionError) as exc:
        raise PromotionError(f"invalid decision JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise PromotionError("decision JSON must contain an object")
    return value, hashlib.sha256(raw).hexdigest()


def _require_file(path: Path, label: str) -> None:
    if not path.exists() or not path.is_file():
        raise PromotionError(f"{label} must be an existing regular file: {path}")
    if path.is_symlink():
        raise PromotionError(f"{label} must not be a symlink: {path}")


def _validate_sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise PromotionError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _validate_decision(
    decision: Mapping[str, Any],
    *,
    accepted_hash: str,
    candidate_hash: str,
    accepted_path: Path,
) -> dict[str, Any]:
    if decision.get("schema_version") != 1:
        raise PromotionError("decision schema_version must be 1")
    if decision.get("decision") != "promote":
        raise PromotionError("decision must explicitly be 'promote'")
    chapter_match = re.fullmatch(r"chapter-(\d+)\.md", accepted_path.name, re.IGNORECASE)
    if chapter_match is None:
        raise PromotionError("accepted chapter must be named chapter-NN.md")
    if decision.get("chapter") != int(chapter_match.group(1)):
        raise PromotionError("decision chapter does not match accepted chapter")
    decision_accepted_hash = _validate_sha(decision.get("accepted_sha256"), "accepted_sha256")
    decision_candidate_hash = _validate_sha(decision.get("candidate_sha256"), "candidate_sha256")
    if decision_accepted_hash != accepted_hash:
        raise PromotionError("accepted chapter SHA-256 does not match frozen decision")
    if decision_candidate_hash != candidate_hash:
        raise PromotionError("candidate SHA-256 does not match frozen decision")

    votes = decision.get("votes")
    if not isinstance(votes, list) or len(votes) != 4:
        raise PromotionError("decision must contain exactly four reader votes")

    readers: set[str] = set()
    revision_votes = 0
    accepted_votes = 0
    for index, vote in enumerate(votes, start=1):
        if not isinstance(vote, dict):
            raise PromotionError(f"reader vote {index} is not an object")
        missing = _REQUIRED_VOTE_FIELDS.difference(vote)
        if missing:
            raise PromotionError(f"reader vote {index} is missing {sorted(missing)}")
        reader = vote["reader"]
        if not isinstance(reader, str) or not reader.strip():
            raise PromotionError(f"reader vote {index} has no reader identity")
        reader_id = reader.strip()
        if reader_id in readers:
            raise PromotionError(f"duplicate reader vote: {reader_id}")
        readers.add(reader_id)
        preference = vote["prefers"]
        if preference == "revision":
            revision_votes += 1
        elif preference == "accepted":
            accepted_votes += 1
        else:
            raise PromotionError(
                f"reader vote {index} has degraded/unknown preference {preference!r}"
            )
        if not isinstance(vote["turn_page"], str) or vote["turn_page"] not in {"yes", "no"}:
            raise PromotionError(
                f"reader vote {index} has degraded turn_page evidence; use yes or no"
            )

    if revision_votes < 3:
        if revision_votes != 2:
            raise PromotionError(
                f"reader panel did not authorize promotion: {revision_votes}/4 prefer revision"
            )
        accepted_defects = decision.get("accepted_concrete_defects")
        candidate_defects = decision.get("candidate_concrete_defects")
        if (
            isinstance(accepted_defects, bool)
            or not isinstance(accepted_defects, int)
            or accepted_defects < 0
            or isinstance(candidate_defects, bool)
            or not isinstance(candidate_defects, int)
            or candidate_defects < 0
        ):
            raise PromotionError(
                "a 2-2 panel split requires non-negative concrete defect counts"
            )
        if candidate_defects >= accepted_defects:
            raise PromotionError(
                "a 2-2 panel split requires the revision to have fewer concrete defects"
            )

    return {
        "revision_votes": revision_votes,
        "accepted_votes": accepted_votes,
        "panel_rule": (
            "at_least_3_of_4_revision"
            if revision_votes >= 3
            else "2_of_4_revision_and_fewer_concrete_defects"
        ),
    }


def _copy_file_exact(source: Path, destination: Path) -> None:
    """Copy bytes and flush them before the destination becomes authoritative."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as source_handle, destination.open("wb") as destination_handle:
        shutil.copyfileobj(source_handle, destination_handle, length=1024 * 1024)
        destination_handle.flush()
        os.fsync(destination_handle.fileno())


def _write_json_atomic(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _remove_if_present(path: Path | None) -> None:
    if path is not None:
        path.unlink(missing_ok=True)


def _link_if_absent(source: Path, destination: Path) -> bool:
    """Create *destination* without replacing an existing path.

    Same-volume hard links provide atomic insertion where the host allows
    them.  Some managed Windows hosts deny hard-link creation, so the helper
    falls back to an exclusive create-and-copy while the cooperative book lock
    is held.  That fallback does not claim protection from a non-cooperating
    writer during the copy.
    """

    try:
        os.link(source, destination)
    except FileExistsError:
        return False
    except PermissionError:
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
        try:
            fd = os.open(destination, flags)
        except FileExistsError:
            return False
        try:
            with source.open("rb") as source_handle, os.fdopen(fd, "wb") as destination_handle:
                shutil.copyfileobj(source_handle, destination_handle, length=1024 * 1024)
                destination_handle.flush()
                os.fsync(destination_handle.fileno())
        except Exception:
            destination.unlink(missing_ok=True)
            raise
    return True


def _restore_holder_if_absent(holder: Path, accepted: Path) -> bool:
    """Restore a holder only when no writer has recreated the canonical path."""

    if not holder.exists():
        return False
    if not _link_if_absent(holder, accepted):
        return False
    holder.unlink(missing_ok=True)
    return True


def _rollback_after_receipt_failure(
    holder: Path,
    accepted: Path,
    candidate_hash: str,
) -> bool:
    """Restore baseline bytes while retaining a concurrent replacement.

    The canonical candidate is moved to a quarantine path before the baseline
    hard link is created.  If another writer has already recreated the
    canonical path, the helper leaves both files in place rather than
    overwriting that writer's bytes.
    """

    if not accepted.exists() or sha256_file(accepted) != candidate_hash:
        return False
    quarantine = accepted.parent / f".{accepted.name}.rollback-{uuid.uuid4().hex}.tmp"
    os.replace(accepted, quarantine)
    try:
        if not _link_if_absent(holder, accepted):
            return False
        holder.unlink(missing_ok=True)
        if quarantine.exists() and sha256_file(quarantine) == candidate_hash:
            quarantine.unlink(missing_ok=True)
        return True
    finally:
        # If a writer recreated the canonical path during rollback, retaining
        # the quarantined bytes is safer than deleting a potentially useful
        # concurrent version.
        if quarantine.exists() and not accepted.exists():
            _restore_holder_if_absent(quarantine, accepted)


def _promote_chapter_locked(
    accepted_path: Path,
    candidate_path: Path,
    decision_path: Path,
    receipt_path: Path,
    *,
    backup_dir: Path | None = None,
    _before_replace: Callable[[], None] | None = None,
) -> dict[str, Any]:
    """Promote *candidate_path* after validating a frozen panel decision.

    ``_before_replace`` is an internal test seam for simulating a concurrent
    edit between staging and the last hash check.  It is intentionally not a
    command-line option.
    """

    accepted_path = Path(accepted_path)
    candidate_path = Path(candidate_path)
    decision_path = Path(decision_path)
    receipt_path = Path(receipt_path)
    _require_file(accepted_path, "accepted chapter")
    _require_file(candidate_path, "candidate chapter")
    _require_file(decision_path, "decision JSON")
    if accepted_path.resolve() == candidate_path.resolve():
        raise PromotionError("accepted and candidate chapters must be different files")
    chapter_paths = {accepted_path.resolve(), candidate_path.resolve()}
    if decision_path.resolve() in chapter_paths:
        raise PromotionError("decision path must be separate from chapter files")
    if receipt_path.resolve() in chapter_paths:
        raise PromotionError("receipt path must be separate from chapter files")

    baseline_hash = sha256_file(accepted_path)
    candidate_hash = sha256_file(candidate_path)
    decision, decision_hash = _read_decision(decision_path)
    panel = _validate_decision(
        decision,
        accepted_hash=baseline_hash,
        candidate_hash=candidate_hash,
        accepted_path=accepted_path,
    )

    if backup_dir is None:
        backup_dir = accepted_path.parent / ".chapter-promotion-backups"
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    if backup_dir.resolve() in {accepted_path.resolve(), candidate_path.resolve()}:
        raise PromotionError("backup directory must be separate from chapter files")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup_path = backup_dir / f"{accepted_path.name}.{stamp}-{uuid.uuid4().hex}.bak"
    holder_path = accepted_path.parent / f".{accepted_path.name}.holder-{uuid.uuid4().hex}.tmp"
    stage_path: Path | None = None
    holder_moved = False
    promoted = False
    retain_holder = False
    retain_backup = False

    try:
        _copy_file_exact(accepted_path, backup_path)
        if sha256_file(accepted_path) != baseline_hash:
            raise PromotionError("accepted chapter changed while creating its snapshot")
        if sha256_file(backup_path) != baseline_hash:
            raise PromotionError("accepted chapter snapshot failed its hash check")

        with tempfile.NamedTemporaryFile(
            mode="wb", dir=accepted_path.parent, prefix=f".{accepted_path.name}.stage-", suffix=".tmp", delete=False
        ) as handle:
            stage_path = Path(handle.name)
        _copy_file_exact(candidate_path, stage_path)
        if sha256_file(stage_path) != candidate_hash:
            raise PromotionError("candidate changed while staging")

        if _before_replace is not None:
            _before_replace()

        if sha256_file(accepted_path) != baseline_hash:
            raise PromotionError("accepted chapter changed before atomic replacement")
        if sha256_file(candidate_path) != candidate_hash:
            raise PromotionError("candidate changed before atomic replacement")
        if sha256_file(decision_path) != decision_hash:
            raise PromotionError("decision JSON changed before atomic replacement")
        if sha256_file(stage_path) != candidate_hash:
            raise PromotionError("staged candidate changed before atomic replacement")

        # Move the accepted inode out of the canonical name first.  This lets
        # us validate the bytes that were actually displaced.  The candidate
        # is then linked into the now-empty name with create-if-absent
        # semantics, so a concurrent writer cannot be overwritten.
        os.replace(accepted_path, holder_path)
        holder_moved = True
        if sha256_file(holder_path) != baseline_hash:
            retain_backup = True
            if _restore_holder_if_absent(holder_path, accepted_path):
                holder_moved = False
            else:
                retain_holder = True
            raise PromotionError("accepted chapter changed before atomic replacement")

        if sha256_file(candidate_path) != candidate_hash:
            raise PromotionError("candidate changed before atomic insertion")
        if sha256_file(decision_path) != decision_hash:
            raise PromotionError("decision JSON changed before atomic insertion")
        if sha256_file(stage_path) != candidate_hash:
            raise PromotionError("staged candidate changed before atomic insertion")

        if not _link_if_absent(stage_path, accepted_path):
            retain_backup = True
            retain_holder = True
            raise PromotionError("accepted chapter appeared before atomic insertion")
        stage_path.unlink(missing_ok=True)
        stage_path = None
        if sha256_file(accepted_path) != candidate_hash:
            retain_backup = True
            retain_holder = True
            raise PromotionError("atomic insertion did not produce the candidate bytes")
        promoted = True

        receipt = {
            "schema_version": 1,
            "status": "promoted",
            "chapter": decision["chapter"],
            "accepted_path": str(accepted_path),
            "candidate_path": str(candidate_path),
            "accepted_sha256_before": baseline_hash,
            "candidate_sha256": candidate_hash,
            "decision_sha256": decision_hash,
            "backup_path": str(backup_path),
            "panel": panel,
            "promoted_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        try:
            _write_json_atomic(receipt_path, receipt)
        except Exception as exc:
            # A promotion without its receipt is not a completed promotion.
            # Restore only while the canonical bytes are still ours.  If a
            # writer changed them, leave that version and retain the holder.
            promoted = False
            if _rollback_after_receipt_failure(holder_path, accepted_path, candidate_hash):
                holder_moved = False
            else:
                retain_holder = True
                retain_backup = True
            raise PromotionError(f"could not save promotion receipt: {exc}") from exc
        return receipt
    except Exception:
        _remove_if_present(stage_path)
        if not promoted:
            if holder_moved and not retain_holder:
                if _restore_holder_if_absent(holder_path, accepted_path):
                    holder_moved = False
                else:
                    retain_holder = True
            if not retain_holder:
                _remove_if_present(holder_path)
            if not retain_backup and not retain_holder:
                _remove_if_present(backup_path)
        if promoted:
            _remove_if_present(holder_path)
        raise


def promote_chapter(
    accepted_path: Path,
    candidate_path: Path,
    decision_path: Path,
    receipt_path: Path,
    *,
    backup_dir: Path | None = None,
    lock_path: Path | None = None,
    _before_replace: Callable[[], None] | None = None,
) -> dict[str, Any]:
    """Promote a chapter under a cooperative single-writer book lock."""

    accepted = Path(accepted_path)
    lock = Path(lock_path) if lock_path is not None else accepted.parent / ".book-genesis-write.lock"
    with _ExclusiveLock(lock):
        return _promote_chapter_locked(
            accepted,
            candidate_path,
            decision_path,
            receipt_path,
            backup_dir=backup_dir,
            _before_replace=_before_replace,
        )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--accepted", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--decision", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--backup-dir", type=Path)
    parser.add_argument("--lock-file", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        receipt = promote_chapter(
            args.accepted,
            args.candidate,
            args.decision,
            args.receipt,
            backup_dir=args.backup_dir,
            lock_path=args.lock_file,
        )
    except (PromotionError, OSError) as exc:
        print(f"promotion rejected: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

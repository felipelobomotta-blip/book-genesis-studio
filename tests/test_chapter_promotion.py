"""Tests for the dependency-free accepted-chapter promotion guard."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPO_ROOT / "skills" / "book-genesis" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

import promote_chapter as promoter  # noqa: E402
from promote_chapter import PromotionError, promote_chapter  # noqa: E402


class ChapterPromotionTests(unittest.TestCase):
    def setUp(self) -> None:
        # The managed Windows sandbox blocks rename/replace inside its OS temp
        # directory.  Keep this test fixture in the checkout so the same
        # atomic-replacement operation used in production is exercised.
        self.root = Path(tempfile.mkdtemp(prefix=".test-chapter-promotion-", dir=REPO_ROOT))
        self.accepted = self.root / "manuscript" / "chapters" / "chapter-35.md"
        self.candidate = self.root / "work" / "attempts" / "chapter-35" / "revision-r4.md"
        self.decision = self.root / "evaluations" / "decisions" / "chapter-35-r4.json"
        self.receipt = self.root / "evaluations" / "promotions" / "chapter-35-r4.json"
        self.backups = self.root / "evaluations" / "backups"
        self.accepted.parent.mkdir(parents=True)
        self.candidate.parent.mkdir(parents=True)
        self.decision.parent.mkdir(parents=True)
        self.accepted.write_text("# Accepted\n\nThe clock held.\n", encoding="utf-8")
        self.candidate.write_text("# Revision\n\nThe clock answered.\n", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def digest(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def write_decision(
        self,
        preferences: list[str],
        *,
        turn_pages: list[str] | None = None,
        accepted_defects: int | None = None,
        candidate_defects: int | None = None,
        accepted_sha: str | None = None,
        candidate_sha: str | None = None,
    ) -> None:
        votes = [
            {
                "reader": f"reader-{index}",
                "prefers": preference,
                "turn_page": (turn_pages or ["yes"] * len(preferences))[index],
            }
            for index, preference in enumerate(preferences)
        ]
        decision: dict[str, object] = {
            "schema_version": 1,
            "chapter": 35,
            "decision": "promote",
            "accepted_sha256": accepted_sha or self.digest(self.accepted),
            "candidate_sha256": candidate_sha or self.digest(self.candidate),
            "votes": votes,
        }
        if accepted_defects is not None:
            decision["accepted_concrete_defects"] = accepted_defects
        if candidate_defects is not None:
            decision["candidate_concrete_defects"] = candidate_defects
        self.decision.write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")

    def promote(self) -> dict[str, object]:
        return promote_chapter(
            self.accepted,
            self.candidate,
            self.decision,
            self.receipt,
            backup_dir=self.backups,
        )

    def test_accepts_three_of_four_and_writes_atomic_receipt_and_snapshot(self) -> None:
        old_bytes = self.accepted.read_bytes()
        self.write_decision(["revision", "revision", "revision", "accepted"])

        receipt = self.promote()

        self.assertEqual(self.candidate.read_bytes(), self.accepted.read_bytes())
        self.assertEqual("promoted", receipt["status"])
        self.assertEqual(self.digest(self.candidate), receipt["candidate_sha256"])
        self.assertEqual(self.digest(self.decision), receipt["decision_sha256"])
        backup = Path(str(receipt["backup_path"]))
        self.assertTrue(backup.is_file())
        self.assertEqual(old_bytes, backup.read_bytes())
        self.assertEqual(receipt, json.loads(self.receipt.read_text(encoding="utf-8")))
        self.assertEqual([], list(self.accepted.parent.glob("*.stage-*.tmp")))

    def test_rejects_two_two_tie_when_defects_are_not_fewer(self) -> None:
        old_bytes = self.accepted.read_bytes()
        self.write_decision(
            ["revision", "revision", "accepted", "accepted"],
            accepted_defects=2,
            candidate_defects=2,
        )

        with self.assertRaisesRegex(PromotionError, "fewer concrete defects"):
            self.promote()

        self.assertEqual(old_bytes, self.accepted.read_bytes())
        self.assertFalse(self.receipt.exists())

    def test_accepts_two_two_tie_when_candidate_has_fewer_defects(self) -> None:
        self.write_decision(
            ["revision", "revision", "accepted", "accepted"],
            accepted_defects=3,
            candidate_defects=1,
        )

        receipt = self.promote()

        self.assertEqual(self.candidate.read_bytes(), self.accepted.read_bytes())
        self.assertEqual("2_of_4_revision_and_fewer_concrete_defects", receipt["panel"]["panel_rule"])

    def test_rejects_missing_or_degraded_votes(self) -> None:
        cases = [
            (["revision", "revision", "revision"], ["yes", "yes", "yes"]),
            (["revision", "revision", "revision", "accepted"], ["yes", "yes", "unsure", "yes"]),
        ]
        for preferences, turn_pages in cases:
            with self.subTest(preferences=preferences, turn_pages=turn_pages):
                old_bytes = self.accepted.read_bytes()
                self.write_decision(preferences, turn_pages=turn_pages)
                with self.assertRaises(PromotionError):
                    self.promote()
                self.assertEqual(old_bytes, self.accepted.read_bytes())
                self.assertFalse(self.receipt.exists())

    def test_rejects_duplicate_reader_identity(self) -> None:
        old_bytes = self.accepted.read_bytes()
        self.write_decision(["revision"] * 4)
        decision = json.loads(self.decision.read_text(encoding="utf-8"))
        decision["votes"][1]["reader"] = decision["votes"][0]["reader"]
        self.decision.write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")

        with self.assertRaisesRegex(PromotionError, "duplicate reader"):
            self.promote()

        self.assertEqual(old_bytes, self.accepted.read_bytes())
        self.assertFalse(self.receipt.exists())

    def test_rejects_candidate_hash_mismatch(self) -> None:
        old_bytes = self.accepted.read_bytes()
        self.write_decision(["revision"] * 4, candidate_sha="0" * 64)

        with self.assertRaisesRegex(PromotionError, "candidate SHA-256"):
            self.promote()

        self.assertEqual(old_bytes, self.accepted.read_bytes())

    def test_rejects_concurrent_accepted_change_after_snapshot(self) -> None:
        old_bytes = self.accepted.read_bytes()
        self.write_decision(["revision"] * 4)

        def race() -> None:
            self.accepted.write_bytes(b"concurrent writer changed this\n")

        with self.assertRaisesRegex(PromotionError, "changed before atomic replacement"):
            promote_chapter(
                self.accepted,
                self.candidate,
                self.decision,
                self.receipt,
                backup_dir=self.backups,
                _before_replace=race,
            )

        self.assertNotEqual(old_bytes, self.accepted.read_bytes())
        self.assertFalse(self.receipt.exists())
        self.assertEqual([], list(self.accepted.parent.glob("*.stage-*.tmp")))
        self.assertEqual([], list(self.backups.glob("*.bak")))

    def test_os_replace_race_preserves_bytes_before_holder_move(self) -> None:
        external_bytes = b"external writer won the race\n"
        self.write_decision(["revision"] * 4)
        real_replace = promoter.os.replace

        def race_replace(source: Path, destination: Path) -> None:
            if Path(source) == self.accepted and ".holder-" in Path(destination).name:
                self.accepted.write_bytes(external_bytes)
            real_replace(source, destination)

        with patch.object(promoter.os, "replace", side_effect=race_replace):
            with self.assertRaisesRegex(PromotionError, "changed before atomic replacement"):
                self.promote()

        self.assertEqual(external_bytes, self.accepted.read_bytes())
        self.assertFalse(self.receipt.exists())
        self.assertEqual(1, len(list(self.backups.glob("*.bak"))))

    def test_recreated_canonical_path_is_not_clobbered_during_insertion(self) -> None:
        external_bytes = b"external writer recreated the chapter\n"
        self.write_decision(["revision"] * 4)
        real_link = promoter._link_if_absent

        def race_link(source: Path, destination: Path) -> bool:
            if Path(destination) == self.accepted and ".stage-" in Path(source).name:
                self.accepted.write_bytes(external_bytes)
            return real_link(source, destination)

        with patch.object(promoter, "_link_if_absent", side_effect=race_link):
            with self.assertRaisesRegex(PromotionError, "appeared before atomic insertion"):
                self.promote()

        self.assertEqual(external_bytes, self.accepted.read_bytes())
        self.assertFalse(self.receipt.exists())
        self.assertEqual(1, len(list(self.backups.glob("*.bak"))))
        self.assertEqual(1, len(list(self.accepted.parent.glob("*.holder-*.tmp"))))

    def test_backup_error_leaves_accepted_chapter_untouched(self) -> None:
        old_bytes = self.accepted.read_bytes()
        self.write_decision(["revision"] * 4)
        with patch.object(promoter, "_copy_file_exact", side_effect=OSError("backup failed")):
            with self.assertRaisesRegex(OSError, "backup failed"):
                self.promote()
        self.assertEqual(old_bytes, self.accepted.read_bytes())
        self.assertFalse(self.receipt.exists())

    def test_receipt_error_rolls_back_the_atomic_promotion(self) -> None:
        old_bytes = self.accepted.read_bytes()
        self.write_decision(["revision"] * 4)
        with patch.object(promoter, "_write_json_atomic", side_effect=OSError("receipt failed")):
            with self.assertRaisesRegex(PromotionError, "could not save promotion receipt"):
                self.promote()
        self.assertEqual(old_bytes, self.accepted.read_bytes())
        self.assertFalse(self.receipt.exists())

    def test_receipt_failure_keeps_new_external_version(self) -> None:
        external_bytes = b"external edit arrived during receipt save\n"
        self.write_decision(["revision"] * 4)

        def fail_after_external_edit(path: Path, value: dict[str, object]) -> None:
            self.accepted.write_bytes(external_bytes)
            raise OSError("receipt failed after external edit")

        with patch.object(promoter, "_write_json_atomic", side_effect=fail_after_external_edit):
            with self.assertRaisesRegex(PromotionError, "could not save promotion receipt"):
                self.promote()

        self.assertEqual(external_bytes, self.accepted.read_bytes())
        self.assertFalse(self.receipt.exists())
        self.assertEqual(1, len(list(self.accepted.parent.glob("*.holder-*.tmp"))))
        self.assertEqual(1, len(list(self.backups.glob("*.bak"))))


if __name__ == "__main__":
    unittest.main()

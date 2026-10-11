"""Bounded waits for proven native subscription refusals with zero model usage.

This is transport evidence, never a model's self-reported reason to retry. Raw
provider envelopes and failed receipts remain immutable physical requests.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re

WAIT_EXIT = 76
MARKER = "BOOK_GENESIS_PROVIDER_WAIT "
MAX_WAIT_SECONDS = 12 * 60 * 60
MAX_DEFERRALS = 8


def quota_wait(envelope, observed_at):
    """Recognize only a zero-usage session limit with an unambiguous UTC reset."""
    if (not isinstance(envelope, dict) or envelope.get("is_error") is not True
            or envelope.get("api_error_status") != 429
            or envelope.get("modelUsage") != {}):
        return None
    usage = envelope.get("usage", {})
    if not isinstance(usage, dict) or any(usage.get(key) != 0 for key in (
            "input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")):
        return None
    match = re.fullmatch(r"You've hit your session limit [·-] resets (\d{1,2})(?::(\d{2}))?(am|pm) \(UTC\)",
                         envelope.get("result", ""))
    if not match or observed_at.tzinfo is None:
        return None
    hour, minute = int(match[1]), int(match[2] or 0)
    if not 1 <= hour <= 12 or not 0 <= minute <= 59:
        return None
    now = observed_at.astimezone(timezone.utc)
    hour = hour % 12 + (12 if match[3] == "pm" else 0)
    reset = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    # Preserve a short grace period for calls made during the reset minute.
    retry = reset + timedelta(seconds=30)
    if retry <= now:
        retry += timedelta(days=1)
    if (retry - now).total_seconds() > MAX_WAIT_SECONDS:
        return None
    return {"provider": "claude.ai", "observed_at": now.isoformat(),
            "retry_at": retry.isoformat(), "reason": envelope["result"]}


def verified_wait(call_dir: Path, receipt, packet):
    """Check a failed physical request before exempting it from model attempts."""
    if receipt.get("status") != "failed" or receipt.get("exit_code") != WAIT_EXIT:
        return None
    sha = lambda data: hashlib.sha256(data).hexdigest()
    if (receipt.get("packet_sha256") != sha(packet)
            or receipt.get("response_sha256") != sha(b"")
            or receipt.get("pending_response_sha256") is not None
            or (call_dir / "response").exists() or (call_dir / "response.pending").exists()):
        raise ValueError("Provider wait has unexpected packet or response evidence")
    for name in ("packet", "stdout", "stderr"):
        if receipt.get(name + "_sha256") != sha((call_dir / name).read_bytes()):
            raise ValueError("Provider wait evidence changed: " + name)
    markers = [line[len(MARKER):] for line in (call_dir / "stderr").read_text(encoding="utf-8").splitlines()
               if line.startswith(MARKER)]
    if len(markers) != 1:
        raise ValueError("Provider wait needs one native transport marker")
    marker = json.loads(markers[0])
    observed = datetime.fromisoformat(marker["observed_at"])
    start, finish = (datetime.fromisoformat(receipt[key]) for key in ("started_at", "finished_at"))
    if not (start - timedelta(seconds=10) <= observed <= finish + timedelta(seconds=10)):
        raise ValueError("Provider wait timestamp differs from its receipt")
    expected = quota_wait(json.loads((call_dir / "stdout").read_bytes()), observed)
    if expected is None or marker != expected:
        raise ValueError("Provider wait is not supported by the original zero-usage refusal")
    return marker

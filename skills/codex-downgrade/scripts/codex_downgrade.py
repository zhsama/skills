#!/usr/bin/env python3
"""
codex_downgrade.py - detect whether a Codex session was served by a different
(usually lower-tier) model than the one you selected.

  session   Offline audit of a local Codex Desktop / Codex CLI session rollout.
  official  Active probe of the official ChatGPT Codex backend via auth.json.

Every check rests on server-stated model identity, never on answer quality.
See README.md for parameters, finding codes and signal provenance.

Exit codes: 0 clean | 2 at risk or unverifiable | 3 confirmed downgrade | 1 error
Python 3.11+, standard library only. Secrets are never printed.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import random
import re
import shutil
import sqlite3
import ssl
import sys
import tempfile
import time
import uuid
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


# ---------------------------------------------------------------------------
# Platform layer
# ---------------------------------------------------------------------------
# ANSI support, console encoding and reading a database another process holds
# open are the only real platform differences, and all of them live here.
IS_WINDOWS = os.name == "nt"

_TEMP_DB_COPIES: List[Path] = []


def enable_ansi() -> bool:
    """Switch on virtual-terminal processing so colour also works in the older
    Windows console host. A no-op everywhere else."""
    if not IS_WINDOWS:
        return True
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        enabled = False
        for handle_id in (-11, -12):  # stdout, stderr
            handle = kernel32.GetStdHandle(handle_id)
            mode = ctypes.c_uint32()
            if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                continue
            if kernel32.SetConsoleMode(handle, mode.value | 0x0004):
                enabled = True
        return enabled
    except Exception:  # noqa: BLE001
        return False


def configure_stdout() -> None:
    """Server text can contain anything. A legacy Windows code page would raise
    UnicodeEncodeError on the way out, which is a silly way to lose a report."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass


def platform_summary() -> str:
    return "%s %s, python %s" % (platform.system() or os.name,
                                 platform.release(), platform.python_version())


def make_ssl_context(insecure: bool, ca_bundle: Optional[str]) -> ssl.SSLContext:
    """One TLS policy for both platforms. Raises on an unusable --ca-bundle so
    the caller can turn that into a finding rather than a stack trace."""
    ctx = ssl.create_default_context()
    if ca_bundle:
        ctx.load_verify_locations(cafile=str(Path(ca_bundle).expanduser()))
    if insecure:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


def open_sqlite_readonly(path: Path) -> Tuple[Optional[sqlite3.Connection], Optional[str]]:
    """Open a SQLite file without taking a write lock. Windows refuses while
    Codex holds the log database open, so fall back to a private temporary copy
    rather than reporting a clean scan that never ran."""
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path
    try:
        return sqlite3.connect(resolved.as_uri() + "?mode=ro", uri=True, timeout=5.0), None
    except (sqlite3.Error, ValueError) as exc:
        first = str(exc)
    try:
        handle, name = tempfile.mkstemp(prefix="codex_downgrade_", suffix=".sqlite")
        os.close(handle)
        copy = Path(name)
        shutil.copyfile(resolved, copy)
        _TEMP_DB_COPIES.append(copy)
        return sqlite3.connect(copy.as_uri() + "?mode=ro", uri=True, timeout=5.0), None
    except Exception as exc:  # noqa: BLE001
        return None, "%s; the temporary-copy fallback also failed: %s" % (first, exc)


def cleanup_temp_copies() -> None:
    while _TEMP_DB_COPIES:
        stale = _TEMP_DB_COPIES.pop()
        try:
            stale.unlink()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Model identity
# ---------------------------------------------------------------------------
# Product tiers used by this audit. Revisions of the same named tier share a rank.
MODEL_TIERS: Dict[str, int] = {
    "gpt-6-astra": 100,
    "gpt-6.1-sol": 90,
    "gpt-6-sol": 90,
    "gpt-5.6-sol": 90,
    "gpt-5.5": 70,
    "gpt-6.1-terra": 65,
    "gpt-5.6-terra": 65,
    "gpt-6-luna": 40,
    "gpt-5.6-luna": 40,
    "gpt-5.4": 38,
    "gpt-5.4-mini": 25,
    "gpt-5.3-codex-spark": 20,
    "gpt-5.2": 15,
}

# Only OpenAI slugs are named. Everything else is one bucket, reported by its
# raw id: this tool has no business ranking other people's line-ups.
OPENAI_PREFIXES: Tuple[str, ...] = (
    "gpt-", "gpt3", "gpt4", "gpt5", "gpt6", "chatgpt", "codex",
    "o1-", "o3-", "o4-", "text-davinci", "davinci", "babbage",
)

# Tokens marking a deliberately smaller or cheaper sibling.
SMALL_MODEL_MARKERS = frozenset({
    "mini", "nano", "small", "tiny", "micro", "lite", "light", "flash",
    "air", "spark", "turbo", "fast", "instant", "haiku",
})
# Tokens marking the larger sibling, so a bigger model is not called a downgrade.
LARGE_MODEL_MARKERS = frozenset({
    "pro", "max", "ultra", "opus", "large", "heavy", "xl",
})

# "5.6" -> (5, 6); "4o" -> (4,) plus a trailing variant token "o".
_VERSION_TOKEN = re.compile(r"^v?(\d+(?:\.\d+)*)([a-z]*)$")
_SLUG_SPLIT = re.compile(r"[-_/:\s]+")
_SERVER_SUFFIX = re.compile(r"[-_](?:\d{4}-\d{2}-\d{2}|codex-abuse-1p)$")

# Response headers Codex itself reads. Captured verbatim when present.
HEADERS_OF_INTEREST: Tuple[str, ...] = (
    "openai-model",
    "x-openai-model",
    "x-codex-safety-buffering-enabled",
    "x-codex-safety-buffering-faster-model",
    "x-codex-primary-used-percent",
    "x-codex-primary-window-minutes",
    "x-codex-primary-reset-at",
    "x-codex-secondary-used-percent",
    "x-codex-secondary-window-minutes",
    "x-codex-secondary-reset-at",
    "x-codex-limit-name",
    "x-codex-active-limit",
    "x-codex-rate-limit-reached-type",
    "x-codex-credits-has-credits",
    "x-codex-credits-unlimited",
    "x-codex-credits-balance",
    "x-codex-promo-message",
    "x-codex-routing-hint",
    "x-codex-turn-state",
    "x-request-id",
    "x-codex-inference-call-id",
    "openai-processing-ms",
    "retry-after",
)

LEVEL_RANK = {"ok": 0, "info": 0, "warn": 1, "critical": 2}

# Findings that prove the server answered as a model you did not select. Kept
# apart from capacity failures: being refused is not being silently swapped.
PROOF_CODES = frozenset({
    "MODEL_DOWNGRADED",
    "MODEL_UPGRADED",
    "MODEL_SAME_TIER",
    "MODEL_MISMATCH",
    "VENDOR_MISMATCH",
    "REROUTE_EVENT_IN_ROLLOUT",
    "PROVIDER_SWITCHED_MID_SESSION",
    "LOG_SERVER_MODEL_MISMATCH",
    "LOG_PROVIDER_FALLBACK",
    "LOG_MODEL_REROUTE_EVENT",
    "MODEL_UNRECOGNIZED",
})

# Findings that mean the check could not reach a conclusion. Serious, but not
# evidence about routing.
INCONCLUSIVE_CODES = frozenset({
    "BACKEND_ERROR",
    "AUTH_EXPIRED",
    "POLICY_REFUSAL",
    "NO_AUTH_FILE",
    "AUTH_UNREADABLE",
    "NO_ACCESS_TOKEN",
    "NO_MODEL",
    "NO_CODEX_HOME",
    "LOGSCAN_SKIPPED",
    "LOGSCAN_UNCORROBORATED",
    "HEADERS_STRIPPED",
    "HEADERS_UNKNOWN",
})



@dataclass
class Finding:
    level: str          # ok | info | warn | critical
    code: str
    message: str
    evidence: Any = None


@dataclass
class Report:
    method: str
    requested_model: Optional[str] = None
    served_model: Optional[str] = None
    findings: List[Finding] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def add(self, level: str, code: str, message: str, evidence: Any = None) -> None:
        self.findings.append(Finding(level, code, message, evidence))

    @property
    def verdict(self) -> Tuple[str, int]:
        codes = {f.code for f in self.findings}
        if "MODEL_DOWNGRADED" in codes:
            return "LOWER MODEL TIER DETECTED", 3
        if codes & PROOF_CODES:
            return "MODEL CHANGE OR REROUTE DETECTED", 3
        critical = {f.code for f in self.findings if f.level == "critical"}
        if critical - INCONCLUSIVE_CODES:
            return "MODEL UNAVAILABLE OR QUOTA EXHAUSTED", 3
        if critical:
            return "CHECK COULD NOT COMPLETE", 2
        # A transport failure that never produced a served model taught us
        # nothing about routing, so do not dress it up as a risk assessment.
        if "BACKEND_ERROR" in codes and not self.served_model:
            return "CHECK COULD NOT COMPLETE", 2
        worst = max((LEVEL_RANK.get(f.level, 0) for f in self.findings), default=0)
        if worst == 1:
            return "AT RISK OR UNVERIFIABLE", 2
        return "NO EVIDENCE OF DOWNGRADE", 0


def parse_slug(slug: str) -> Dict[str, Any]:
    """Take a model slug apart without needing it to be recorded anywhere, so
    an unrecorded model stays comparable: 'gpt-5.7-mini' parses as openai,
    family gpt, version (5, 7), size marker 'mini'."""
    key = (slug or "").strip().lower()
    out: Dict[str, Any] = {"vendor": None, "family": None, "line": None,
                           "version": (), "variant": None,
                           "size_marker": None, "large_marker": None}
    if not key:
        return out

    out["vendor"] = "openai" if any(key.startswith(p) for p in OPENAI_PREFIXES) else "other"

    tokens = [t for t in _SLUG_SPLIT.split(key) if t]
    if not tokens:
        return out
    out["family"] = tokens[0]

    version_at: Optional[int] = None
    version_suffix = ""
    for i, tok in enumerate(tokens):
        if i == 0:
            continue
        match = _VERSION_TOKEN.match(tok)
        if not match:
            continue
        try:
            out["version"] = tuple(int(p) for p in match.group(1).split("."))
        except ValueError:
            continue
        version_suffix = match.group(2)
        version_at = i
        break

    if version_at is None:
        out["line"] = "-".join(tokens)
        tail = tokens[1:]
    else:
        out["line"] = "-".join(tokens[:version_at])
        tail = ([version_suffix] if version_suffix else []) + tokens[version_at + 1:]
    out["variant"] = "-".join(tail) or None

    # Scan every token after the family name: size markers live in the tail
    # ('gpt-5.4-mini') but also mid-slug ('claude-opus-5').
    for tok in tokens[1:]:
        if tok in SMALL_MODEL_MARKERS and not out["size_marker"]:
            out["size_marker"] = tok
        if tok in LARGE_MODEL_MARKERS and not out["large_marker"]:
            out["large_marker"] = tok
    return out


@dataclass
class ModelIdentity:
    """Everything the tool managed to work out about one model slug."""
    slug: str
    normalized: str = ""
    known: bool = False
    source: str = "unknown"        # tier-table | catalog | inferred | unknown
    base: Optional[str] = None     # recorded slug this one extends, if any
    suffix: Optional[str] = None   # server-side suffix beyond that base
    vendor: Optional[str] = None
    family: Optional[str] = None
    line: Optional[str] = None
    version: Tuple[int, ...] = ()
    variant: Optional[str] = None
    size_marker: Optional[str] = None
    large_marker: Optional[str] = None
    tier: Optional[int] = None
    tier_source: Optional[str] = None
    catalog_priority: Optional[int] = None
    context_window: Optional[int] = None
    display_name: Optional[str] = None

    def version_str(self) -> str:
        return ".".join(str(x) for x in self.version) if self.version else "?"

    def describe(self) -> str:
        """Short provenance string, quoted inside finding messages."""
        if self.source == "tier-table":
            return "ranked %s in the %s" % (self.tier, self.tier_source or "tier table")
        if self.source == "catalog":
            bits = ["in your model catalog"]
            if self.catalog_priority is not None:
                bits.append("priority %d" % self.catalog_priority)
            if self.tier is not None:
                bits.append("rank %d" % self.tier)
            return ", ".join(bits)
        if self.source == "inferred":
            bits = [] if self.vendor == "openai" else ["not an OpenAI slug"]
            if self.version:
                bits.append("v%s" % self.version_str())
            if self.size_marker:
                bits.append("'%s' size marker" % self.size_marker)
            return "unrecorded, inferred from the slug (%s)" % (", ".join(bits) or "shape only")
        return "unrecorded and unparseable"


class ModelRegistry:
    """Use the catalog for identity metadata and explicit ranks for tier comparisons."""

    def __init__(self) -> None:
        self.tiers: Dict[str, int] = dict(MODEL_TIERS)
        self.user_tiers: Dict[str, int] = {}
        self.catalog: Dict[str, Dict[str, Any]] = {}
        self.catalog_path: Optional[str] = None
        self.catalog_meta: Dict[str, Any] = {}
        self.notes: List[Tuple[str, str, str]] = []
        self._cache: Dict[str, ModelIdentity] = {}

    # -- construction --------------------------------------------------------
    @classmethod
    def build(cls, codex_home: Optional[Path], cfg: Optional[Dict[str, Any]] = None,
              catalog_path: Optional[str] = None,
              tier_map_path: Optional[str] = None) -> "ModelRegistry":
        reg = cls()
        cfg = cfg or {}
        candidates: List[Path] = []
        if catalog_path:
            candidates.append(Path(catalog_path).expanduser())
        else:
            from_cfg = cfg.get("model_catalog_json")
            if isinstance(from_cfg, str) and from_cfg.strip():
                candidates.append(Path(from_cfg).expanduser())
            if codex_home:
                candidates.append(Path(codex_home) / "models_cache.json")
        for path in candidates:
            if reg._load_catalog(path):
                break
        else:
            reg.notes.append((
                "info", "NO_MODEL_CATALOG",
                "No model catalog was loaded (looked at: %s). Slug recognition falls back "
                "to the built-in table. Use --model-catalog to supply catalog metadata "
                "or --tier-map to rank additional models."
                % (", ".join(str(p) for p in candidates) or "nowhere")))
        if tier_map_path:
            reg._load_tier_map(Path(tier_map_path).expanduser())
        return reg

    def _load_catalog(self, path: Path) -> bool:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, NotADirectoryError, IsADirectoryError):
            return False
        except Exception as exc:  # noqa: BLE001
            self.notes.append(("warn", "MODEL_CATALOG_UNREADABLE",
                               "Model catalog %s could not be parsed (%s). Falling back to "
                               "the built-in table." % (path, exc)))
            return False
        entries = raw.get("models") if isinstance(raw, dict) else raw
        if not isinstance(entries, list):
            self.notes.append(("warn", "MODEL_CATALOG_UNREADABLE",
                               "Model catalog %s has no 'models' list." % path))
            return False
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            slug = entry.get("slug") or entry.get("id") or entry.get("name")
            if isinstance(slug, str) and slug.strip():
                self.catalog[slug.strip().lower()] = entry
        if not self.catalog:
            return False
        self.catalog_path = str(path)
        if isinstance(raw, dict):
            self.catalog_meta = {"fetched_at": raw.get("fetched_at"),
                                 "client_version": raw.get("client_version")}
        return True

    def _load_tier_map(self, path: Path) -> None:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            self.notes.append(("warn", "TIER_MAP_UNREADABLE",
                               "--tier-map %s could not be read (%s); ignoring it." % (path, exc)))
            return
        if not isinstance(raw, dict):
            self.notes.append(("warn", "TIER_MAP_UNREADABLE",
                               "--tier-map %s must be a JSON object mapping a model slug to "
                               "an integer rank." % path))
            return
        for slug, rank in raw.items():
            try:
                self.user_tiers[slug.strip().lower()] = int(str(rank))
            except ValueError:
                self.notes.append(("warn", "TIER_MAP_INVALID_RANK",
                                   "Ignoring non-integer rank for '%s' in %s." % (slug, path)))
        self._cache.clear()
        self.notes.append(("info", "TIER_MAP_LOADED",
                           "Loaded %d custom model rank(s) from %s."
                           % (len(self.user_tiers), path)))

    # -- lookup --------------------------------------------------------------
    def _match_recorded(self, key: str) -> Optional[Tuple[str, str]]:
        """Only dated snapshots and the known routing suffix inherit a base tier."""
        bases = (key, _SERVER_SUFFIX.sub("", key))
        for base in bases:
            if base in self.user_tiers:
                return base, "tier-table"
            if base in self.tiers:
                return base, "catalog" if base in self.catalog else "tier-table"
        for base in bases:
            if base in self.catalog:
                return base, "catalog"
        return None

    def identify(self, slug: Optional[str]) -> Optional[ModelIdentity]:
        if not slug or not str(slug).strip():
            return None
        key = str(slug).strip().lower()
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        ident = ModelIdentity(slug=str(slug).strip(), normalized=key)
        matched = self._match_recorded(key)
        if matched:
            base, source = matched
            ident.known = True
            ident.source = source
            ident.base = base
            if len(key) > len(base):
                ident.suffix = key[len(base):].lstrip("-_")
            entry = self.catalog.get(base)
            if entry:
                priority = entry.get("priority")
                ident.catalog_priority = priority if isinstance(priority, int) else None
                window = entry.get("context_window") or entry.get("max_context_window")
                ident.context_window = window if isinstance(window, int) else None
                name = entry.get("display_name")
                ident.display_name = name if isinstance(name, str) else None

        parsed = parse_slug(ident.base or key)
        ident.vendor = parsed["vendor"]
        ident.family = parsed["family"]
        ident.line = parsed["line"]
        ident.version = parsed["version"]
        ident.variant = parsed["variant"]
        ident.size_marker = parsed["size_marker"]
        ident.large_marker = parsed["large_marker"]

        for candidate in (key, ident.base):
            if not candidate:
                continue
            if candidate in self.user_tiers:
                ident.tier, ident.tier_source = self.user_tiers[candidate], "tier-map"
                break
            if candidate in self.tiers:
                ident.tier, ident.tier_source = self.tiers[candidate], "tier table"
                break

        if not ident.known and (ident.vendor or ident.version):
            ident.source = "inferred"
        self._cache[key] = ident
        return ident

    def window_owners(self, window: int) -> List[str]:
        """Catalog slugs whose context window equals the given size. Lets the
        session audit name the model a reported window actually belongs to."""
        owners = []
        for slug, entry in self.catalog.items():
            if entry.get("context_window") == window or entry.get("max_context_window") == window:
                owners.append(slug)
        return sorted(owners)

    def describe(self) -> Dict[str, Any]:
        return {
            "catalog_path": self.catalog_path,
            "catalog_models": len(self.catalog),
            "catalog_fetched_at": self.catalog_meta.get("fetched_at"),
            "catalog_client_version": self.catalog_meta.get("client_version"),
            "builtin_ranks": len(self.tiers),
            "custom_ranks": len(self.user_tiers),
        }

    def apply_notes(self, report: "Report") -> None:
        for level, code, message in self.notes:
            report.add(level, code, message)


def backend_family(response_id: Optional[str]) -> str:
    """Fingerprint the upstream vendor from the id shape. A relay that swaps
    the upstream provider usually forgets to rewrite the id it returns."""
    if not response_id:
        return "unknown"
    rid = response_id.strip()
    if rid.startswith("resp_"):
        return "openai-responses"
    if rid.startswith("chatcmpl-"):
        return "openai-chat-completions"
    if rid.startswith("msg_01"):
        return "anthropic-messages"
    if rid.startswith("msg_"):
        return "openai-or-anthropic-message-item"
    if rid.startswith("gen-"):
        return "openrouter"
    return "unrecognized"


def classify_endpoint(base_url: Optional[str]) -> str:
    if not base_url:
        return "official-chatgpt"
    u = base_url.lower()
    if "chatgpt.com/backend-api" in u:
        return "official-chatgpt"
    if "api.openai.com" in u:
        return "official-api"
    return "third-party"


def default_codex_home() -> Path:
    """$CODEX_HOME wins on both systems; otherwise ~/.codex, resolved through
    expanduser so it works with USERPROFILE on Windows and HOME on Linux."""
    env = os.environ.get("CODEX_HOME")
    if env and env.strip():
        return Path(env).expanduser()
    return Path(os.path.expanduser("~")) / ".codex"



# ---------------------------------------------------------------------------
# Shared verdict logic for an observed (requested, served) pair
# ---------------------------------------------------------------------------
def judge_served_model(report: Report, requested: str, served: Optional[str],
                       evidence: Any = None, status: Optional[int] = None,
                       registry: Optional[ModelRegistry] = None) -> None:
    """Report the observed identity change. Compare tiers only when both are ranked."""
    if not served and status is not None and status >= 400:
        report.add(
            "info", "NO_SERVED_MODEL_HTTP_ERROR",
            "No served model to compare: the request failed with HTTP %d before the "
            "model produced anything. Judge this run by the HTTP finding above." % status,
            evidence)
        return

    if not served:
        report.add(
            "warn", "NO_SERVED_MODEL",
            "No 'openai-model' header and no response.model, so the served model "
            "cannot be verified.",
            evidence)
        return

    registry = registry or ModelRegistry()
    report.served_model = served
    rid = registry.identify(requested)
    sid = registry.identify(served)
    report.details["requested_identity"] = asdict(rid) if rid else None
    report.details["served_identity"] = asdict(sid) if sid else None

    if rid is not None and not rid.known:
        report.add(
            "info", "REQUESTED_MODEL_UNRECORDED",
            "Requested model '%s' has no local rank (%s). Supply --tier-map to rank it."
            % (requested, rid.describe()))

    if served.strip().lower() == requested.strip().lower():
        report.add("ok", "MODEL_MATCH",
                   "Server reported model '%s', which matches the requested model." % served,
                   evidence)
        if sid is not None and not sid.known:
            report.add(
                "info", "MODEL_UNRECORDED",
                "That slug is recorded nowhere local, so the name matches but nothing "
                "corroborates what it denotes.")
        return

    # --- same model, server-side variant ---------------------------------
    if rid and sid and rid.base and rid.base == sid.base:
        report.add(
            "warn", "MODEL_VARIANT",
            "Server reported '%s' while you requested '%s': the same base model with a "
            "server-side variant suffix." % (served, requested),
            evidence)
        return

    # --- a slug that resolves to nothing at all ---------------------------
    if sid is not None and not sid.known and not sid.version and not sid.variant:
        report.add(
            "critical", "MODEL_UNRECOGNIZED",
            "Requested '%s' but the server reported the unrecognized slug '%s'. "
            "Its tier is unknown." % (requested, served),
            evidence)
        return

    # --- one side is an OpenAI model and the other is not -----------------
    if rid and sid and rid.vendor != sid.vendor:
        report.add(
            "critical", "VENDOR_MISMATCH",
            "Requested '%s' but the server served '%s'. One is an OpenAI model and the "
            "other is not, so this is a substitution, not a tier change."
            % (requested, served),
            evidence)
        return

    rtier = rid.tier if rid else None
    stier = sid.tier if sid else None
    if rtier is None or stier is None:
        report.add(
            "critical", "MODEL_MISMATCH",
            "Requested '%s' but the server served '%s'. Tier direction is unknown. "
            "Supply missing ranks with --tier-map." % (requested, served), evidence)
        return

    if stier < rtier:
        level, code, direction = "critical", "MODEL_DOWNGRADED", "lower"
    elif stier > rtier:
        level, code, direction = "warn", "MODEL_UPGRADED", "higher"
    else:
        level, code, direction = "warn", "MODEL_SAME_TIER", "same"
    report.add(level, code,
               "Requested '%s' (rank %d) but the server served '%s' (rank %d). "
               "Serving tier: %s." % (requested, rtier, served, stier, direction), evidence)


def judge_headers(report: Report, headers: Dict[str, str]) -> None:
    """Apply the safety-buffering and quota rules to a captured header set."""
    faster = headers.get("x-codex-safety-buffering-faster-model")
    enabled = headers.get("x-codex-safety-buffering-enabled", "(absent)")
    if faster:
        report.add(
            "warn", "SAFETY_BUFFERING_ARMED",
            "Safety buffering is armed: the server named '%s' as the faster fallback "
            "model (enabled = %s). enabled=false does not disable it." % (faster, enabled),
            {"faster_model": faster, "enabled": enabled})

    reached = headers.get("x-codex-rate-limit-reached-type")
    if reached:
        report.add("critical", "RATE_LIMIT_REACHED",
                   "Server reported x-codex-rate-limit-reached-type = '%s'; quota "
                   "exhaustion is the documented fallback trigger." % reached,
                   {"rate_limit_reached_type": reached})

    for scope in ("primary", "secondary"):
        raw = headers.get("x-codex-%s-used-percent" % scope)
        if raw is None:
            continue
        try:
            pct = float(raw)
        except ValueError:
            continue
        window = headers.get("x-codex-%s-window-minutes" % scope, "?")
        level = "ok"
        if pct >= 100.0:
            level = "critical"
        elif pct >= 90.0:
            level = "warn"
        report.add(level, "QUOTA_%s" % scope.upper(),
                   "%s quota window is %.1f%% used over %s minutes." % (scope.capitalize(), pct, window),
                   {"used_percent": pct, "window_minutes": window})



# Header groups the verdict leans on. A stripped set looks exactly like a clean
# one, so absence is always stated rather than passed over. README.md lists the
# individual headers behind each group.
REQUIRED_HEADER_GROUPS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("quota", ("x-codex-primary-used-percent", "x-codex-secondary-used-percent")),
    ("fallback-state", ("x-codex-safety-buffering-enabled",
                        "x-codex-safety-buffering-faster-model")),
    ("request-id", ("x-request-id", "x-codex-inference-call-id")),
)


def judge_required_headers(report: Report, headers: Dict[str, str],
                           endpoint_class: str, answered: bool) -> None:
    """State whether the routing headers arrived, were stripped, or were never
    seen. Staying silent about a missing header reads the same as a clean pass."""
    if not answered:
        report.add("warn", "HEADERS_UNKNOWN",
                   "No successful response, so no routing header could be read and every "
                   "header-based check was skipped.")
        return

    present = [name for name, keys in REQUIRED_HEADER_GROUPS
               if any(headers.get(k) for k in keys)]
    missing = [name for name, _ in REQUIRED_HEADER_GROUPS if name not in present]
    evidence = {"present": present, "missing": missing, "headers_seen": sorted(headers)}

    if not missing:
        report.add("ok", "HEADERS_PRESENT",
                   "Every routing header group arrived: %s." % ", ".join(present), evidence)
        return

    if endpoint_class == "official-api":
        report.add("info", "HEADERS_UNKNOWN",
                   "Header group(s) %s absent. api.openai.com does not emit the x-codex-* "
                   "headers, so quota and fallback state are unverifiable here even though "
                   "the served model is not." % ", ".join(missing), evidence)
        return

    if endpoint_class == "third-party":
        report.add("warn", "HEADERS_STRIPPED",
                   "Header group(s) %s absent. A relay that drops these leaves no way to "
                   "verify quota-driven fallback, and it also decides what the headers it "
                   "does send say." % ", ".join(missing), evidence)
        return

    report.add("critical" if not present else "warn", "HEADERS_STRIPPED",
               "Header group(s) %s absent from an official ChatGPT Codex response. These "
               "normally accompany every reply, so something in the path is stripping them "
               "and routing state cannot be confirmed." % ", ".join(missing), evidence)


def judge_session_headers(report: Report, session: Dict[str, Any], sid: str,
                          endpoint_class: str) -> None:
    """Rollout-side counterpart. Codex only records a quota snapshot when the
    response actually carried the x-codex-*-used-percent headers."""
    total = session["rate_snapshots_total"]
    populated = session["rate_snapshots_populated"]
    evidence = {"snapshots_total": total, "snapshots_populated": populated}

    if populated:
        report.add("ok", "HEADERS_PRESENT",
                   "Session %s recorded %d populated quota snapshot(s), so the routing "
                   "headers did reach the client." % (sid, populated), evidence)
        return
    if total == 0:
        report.add("warn", "HEADERS_UNKNOWN",
                   "Session %s recorded no quota snapshot at all, so this rollout reflects "
                   "no routing header and header-based verification could not run." % sid,
                   evidence)
        return
    report.add("warn" if endpoint_class == "third-party" else "critical", "HEADERS_STRIPPED",
               "All %d quota snapshots in session %s are empty. Codex fills them from the "
               "x-codex-*-used-percent headers, so those headers never arrived."
               % (total, sid), evidence)


# ---------------------------------------------------------------------------
# METHOD 1 -- offline session audit
# ---------------------------------------------------------------------------
ROLLOUT_PREFILTER = re.compile(
    r'"(session_meta|turn_context|token_usage_record|token_count|model_reroute'
    r'|safety_buffering|thread_settings_applied|turn_aborted)"')


def read_config(codex_home: Path) -> Dict[str, Any]:
    path = codex_home / "config.toml"
    if not path.is_file() or tomllib is None:
        return {}
    try:
        with path.open("rb") as fh:
            return tomllib.load(fh)
    except Exception:
        return {}


def find_rollouts(codex_home: Path, session_id: Optional[str], limit: int) -> List[Path]:
    root = codex_home / "sessions"
    if not root.is_dir():
        return []
    files = list(root.rglob("rollout-*.jsonl"))
    if session_id:
        needle = session_id.strip().lower()
        matched = [p for p in files if needle in p.name.lower()]
        return sorted(matched)
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[:limit]


def _ordered(values: Iterable[Any]) -> List[str]:
    """Distinct non-empty strings, first-seen order."""
    out: List[str] = []
    for value in values:
        if isinstance(value, str) and value and value not in out:
            out.append(value)
    return out


def parse_rollout(path: Path) -> Dict[str, Any]:
    meta: Dict[str, Any] = {}
    turn_models: List[str] = []
    response_ids: List[str] = []
    rate_snapshots: List[Any] = []
    context_windows: List[int] = []
    reroute_events: List[Any] = []
    settings: List[Dict[str, Any]] = []
    aborts: Dict[str, int] = {}
    quota_alias: List[str] = []
    peak_used = 0.0

    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if not line.strip() or not ROLLOUT_PREFILTER.search(line):
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            kind = obj.get("type")
            payload = obj.get("payload") or {}

            if kind == "session_meta":
                meta = payload
            elif kind == "turn_context":
                m = payload.get("model")
                if m and m not in turn_models:
                    turn_models.append(m)
            elif kind == "token_usage_record":
                rid = payload.get("response_id")
                if rid:
                    response_ids.append(rid)
            elif kind == "event_msg":
                ptype = payload.get("type")
                if ptype == "token_count":
                    limits = payload.get("rate_limits")
                    if "rate_limits" in payload:
                        rate_snapshots.append(limits)
                    if isinstance(limits, dict):
                        alias = limits.get("normal_model_slug")
                        if isinstance(alias, str) and alias not in quota_alias:
                            quota_alias.append(alias)
                        for key in ("primary", "secondary"):
                            window = limits.get(key)
                            if isinstance(window, dict):
                                pct = window.get("used_percent")
                                if isinstance(pct, (int, float)):
                                    peak_used = max(peak_used, float(pct))
                    info = payload.get("info") or {}
                    cw = info.get("model_context_window")
                    if isinstance(cw, int):
                        context_windows.append(cw)
                elif ptype == "thread_settings_applied":
                    snap = payload.get("thread_settings") or {}
                    # Only the routing scalars are lifted. The rest of the
                    # snapshot carries cwd and permission paths.
                    row = {"model": snap.get("model"),
                           "provider": snap.get("model_provider_id"),
                           "service_tier": snap.get("service_tier")}
                    if row not in settings:
                        settings.append(row)
                elif ptype == "turn_aborted":
                    reason = payload.get("reason")
                    if not isinstance(reason, str):
                        reason = json.dumps(reason, default=str)
                    aborts[reason] = aborts.get(reason, 0) + 1
                elif ptype and ("reroute" in ptype or "safety_buffering" in ptype):
                    reroute_events.append(payload)

    families: Dict[str, int] = {}
    for rid in response_ids:
        fam = backend_family(rid)
        families[fam] = families.get(fam, 0) + 1

    populated = sum(1 for s in rate_snapshots
                    if isinstance(s, dict) and (s.get("primary") or s.get("secondary")))

    return {
        "file": str(path),
        "session_id": meta.get("id") or meta.get("session_id"),
        "cli_version": meta.get("cli_version"),
        "originator": meta.get("originator"),
        "session_provider": meta.get("model_provider"),
        "turn_models": turn_models,
        "backend_families": families,
        "context_windows": sorted(set(context_windows)),
        "rate_snapshots_total": len(rate_snapshots),
        "rate_snapshots_populated": populated,
        "reroute_events": reroute_events,
        "settings_models": _ordered(r.get("model") for r in settings),
        "settings_providers": _ordered(r.get("provider") for r in settings),
        "service_tiers": _ordered(r.get("service_tier") for r in settings),
        "quota_alias_models": quota_alias,
        "turn_aborts": aborts,
        "peak_used_percent": round(peak_used, 1),
    }



LOG_PATTERNS = (
    # (code, level, LIKE fragment, message)
    ("LOG_SERVER_MODEL_MISMATCH", "critical", "%while requested model was%",
     "Codex logged a server/requested model mismatch, which it only does on a "
     "confirmed reroute."),
    ("LOG_PROVIDER_FALLBACK", "critical", "%replaced unavailable requested model%",
     "Codex replaced the requested model with the provider default because the "
     "requested model was unavailable."),
    ("LOG_MODEL_REROUTE_EVENT", "critical", "%ModelReroute%",
     "A ModelReroute event was recorded."),
    ("LOG_SAFETY_BUFFERING", "warn", "%SafetyBuffering%",
     "A safety-buffering event was recorded: the server offered a faster fallback "
     "model for that turn."),
    ("LOG_MODEL_MATCH", "ok", "%matches requested model%",
     "Codex confirmed the server-reported model matched the requested model."),
)

# Rows that merely quote a command or a transcript would otherwise match our own
# search terms, so they are excluded.
LOG_NOISE_FRAGMENTS = ("%ToolCall:%", "%exec_command%", "%Submission sub=%")

# Modules that log conversation content - streamed output items, reasoning,
# tool calls - rather than routing decisions. Their rows quote whatever the
# session happened to discuss, so a session about model routing would otherwise
# report itself as a reroute. Reroute warnings come from the session modules.
LOG_NOISE_TARGETS = ("codex_core::stream_events_utils",)

# The log table is not identical across Codex versions or packaging, so the
# message, timestamp and module columns are probed rather than assumed.
LOG_BODY_COLUMNS = ("feedback_log_body", "log_body", "body", "message")
LOG_TIME_COLUMNS = ("ts", "timestamp", "time", "created_at")
LOG_TARGET_COLUMNS = ("target", "module_path", "module")


def log_schema(con: sqlite3.Connection) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    try:
        rows = con.execute("select name from pragma_table_info('logs')").fetchall()
    except sqlite3.Error:
        return None, None, None
    names = {str(r[0]) for r in rows}
    body = next((c for c in LOG_BODY_COLUMNS if c in names), None)
    stamp = next((c for c in LOG_TIME_COLUMNS if c in names), None)
    target = next((c for c in LOG_TARGET_COLUMNS if c in names), None)
    return body, stamp, target


def log_window_floor(con: sqlite3.Connection, time_col: str,
                     hours: int) -> Tuple[Any, Any]:
    """Lower bound for the time window, plus the newest row's stamp. The unit
    is inferred from that newest value, because guessing wrong returns zero rows
    and would look exactly like a clean result."""
    newest = None
    try:
        row = con.execute("select %s from logs order by rowid desc limit 1" % time_col).fetchone()
        if row:
            newest = row[0]
    except sqlite3.Error:
        return None, None

    now = time.time()
    if isinstance(newest, bool):
        return None, newest
    if isinstance(newest, (int, float)):
        if newest > 1e12:  # milliseconds
            return int((now - hours * 3600) * 1000), newest
        return int(now - hours * 3600), newest
    if isinstance(newest, str):
        floor = datetime.now(timezone.utc) - timedelta(hours=hours)
        return floor.strftime("%Y-%m-%dT%H:%M:%S"), newest
    return None, newest


def scan_logs(codex_home: Path, hours: int, report: Report) -> None:
    dbs = sorted(codex_home.glob("logs_*.sqlite"),
                 key=lambda p: p.stat().st_mtime, reverse=True)
    if not dbs:
        report.add("info", "LOGSCAN_NO_DB",
                   "No logs_*.sqlite database found in %s." % codex_home)
        return

    db = dbs[0]
    con, failure = open_sqlite_readonly(db)
    if con is None:
        report.add("warn", "LOGSCAN_FAILED",
                   "Could not open %s read-only (%s), so local log evidence was not "
                   "checked. That is missing evidence, not a clean result."
                   % (db.name, failure))
        return

    try:
        body_col, time_col, target_col = log_schema(con)
        if not body_col:
            report.add("warn", "LOGSCAN_SCHEMA_UNKNOWN",
                       "The log database %s has no recognisable message column (looked for "
                       "%s). This build stores logs differently, so judge the session by "
                       "the rollout evidence above."
                       % (db.name, ", ".join(LOG_BODY_COLUMNS)))
            return

        floor: Any = None
        newest: Any = None
        if time_col:
            floor, newest = log_window_floor(con, time_col, hours)

        noise = "".join(" and " + body_col + " not like '" + fragment + "'"
                        for fragment in LOG_NOISE_FRAGMENTS)
        if target_col:
            noise += "".join(" and coalesce(" + target_col + ", '') <> '" + name + "'"
                             for name in LOG_NOISE_TARGETS)
        if floor is None:
            where = " where " + body_col + " like ?" + noise
            window = "the whole database (no usable timestamp column)"
        else:
            where = " where " + time_col + " >= ? and " + body_col + " like ?" + noise
            window = "the last %dh" % hours

        def query(select: str, like: str, suffix: str = "") -> Any:
            args = (like,) if floor is None else (floor, like)
            return con.execute(select + where + suffix, args)

        hits = 0
        for code, level, like, message in LOG_PATTERNS:
            try:
                (count,) = query("select count(*) from logs", like).fetchone()
            except sqlite3.Error:
                continue
            if not count:
                continue
            hits += 1
            sample = ""
            try:
                row = query("select substr(replace(" + body_col + ", char(10), ' '), 1, 400) "
                            "from logs", like, " order by rowid desc limit 1").fetchone()
                if row:
                    sample = row[0]
            except sqlite3.Error:
                pass
            report.add(level, code, "%s Matches in %s: %d." % (message, window, count), sample)

        if hits == 0:
            # Nothing matched, which has two very different causes. The client
            # only compares models when the server sends the openai-model
            # header; with no header it logs neither agreement nor mismatch.
            # So silence in a populated window means the check never ran.
            try:
                (rows,) = query("select count(*) from logs", "%").fetchone()
            except sqlite3.Error:
                rows = 0
            trailer = " Newest log row is stamped %s." % newest if newest is not None else ""
            if rows:
                report.add("warn", "LOGSCAN_UNCORROBORATED",
                           "%d log rows in %s, but not one records the client comparing the "
                           "served model against the requested one. It logs that comparison "
                           "on every response that carries the openai-model header, in "
                           "agreement as well as in mismatch, so the absence of both means "
                           "the header never arrived and the client's own verification never "
                           "ran. This is missing evidence, not a clean result.%s"
                           % (rows, window, trailer))
            else:
                report.add("info", "LOGSCAN_EMPTY_WINDOW",
                           "No log rows at all in %s, so there was nothing to scan. Widen "
                           "--log-hours if the install is older than the window.%s"
                           % (window, trailer))
    finally:
        con.close()
        cleanup_temp_copies()



# Quota pressure is not itself a downgrade, but it is the condition under which
# a backend is most likely to answer with something cheaper.
QUOTA_PRESSURE_PERCENT = 90.0

# TurnAbortReason, serialized snake_case. Only budget exhaustion bears on routing.
ABORT_NOTES = {
    "budget_limited": ("warn", "the turn ran out of its budget"),
    "interrupted": ("info", "you interrupted the turn"),
    "replaced": ("info", "a newer turn replaced it"),
    "review_ended": ("info", "a review turn finished"),
}


def judge_session_settings(report: Report, s: Dict[str, Any], sid: str) -> None:
    """Findings drawn from thread_settings_applied, quota metadata and aborts.

    thread_settings_applied is the client's own record of the settings it put
    into effect; turn_context is what it then sent. Comparing the two catches a
    substitution made before the request ever left the machine."""
    settings_models = s["settings_models"]
    turn_models = s["turn_models"]

    providers = s["settings_providers"]
    if len(providers) > 1:
        report.add("critical", "PROVIDER_SWITCHED_MID_SESSION",
                   "Session %s changed model provider mid-thread (%s). Some turns were "
                   "answered by a different endpoint than others."
                   % (sid, ", ".join(providers)), providers)

    if settings_models and turn_models:
        unsettled = [m for m in turn_models if m not in settings_models]
        if unsettled:
            report.add("warn", "SETTINGS_MODEL_DIVERGENCE",
                       "Session %s sent turn(s) for model(s) %s that no applied thread "
                       "settings ever named (settings named %s). The client sent something "
                       "other than what it recorded as selected."
                       % (sid, ", ".join(unsettled), ", ".join(settings_models)),
                       {"turn_models": turn_models, "settings_models": settings_models})

        unused = [m for m in settings_models if m not in turn_models]
        if unused:
            report.add("info", "SETTINGS_MODEL_UNUSED",
                       "Session %s applied settings for model(s) %s that ran no turn. "
                       "Switching models, and automatic review turns, both do this."
                       % (sid, ", ".join(unused)), unused)

    if s["service_tiers"]:
        report.add("info", "SERVICE_TIER_RECORDED",
                   "Session %s recorded service tier(s) %s. Tier governs how a request is "
                   "served, not which model answers it."
                   % (sid, ", ".join(s["service_tiers"])), s["service_tiers"])

    alias = [m for m in s["quota_alias_models"] if m not in turn_models]
    if alias:
        report.add("info", "QUOTA_ALIAS_MODEL",
                   "Session %s carried quota metadata naming %s. Upstream documents this "
                   "as the normal model for a quota alias and explicitly not a replacement "
                   "for the requested model, so it is not evidence of a swap."
                   % (sid, ", ".join(alias)), s["quota_alias_models"])

    peak = s["peak_used_percent"]
    if peak >= QUOTA_PRESSURE_PERCENT:
        report.add("warn", "QUOTA_PRESSURE_RECORDED",
                   "Session %s reached %.1f%% of a rate-limit window. Not a downgrade by "
                   "itself, but near a limit is when a backend is most likely to answer "
                   "with a cheaper model." % (sid, peak), {"peak_used_percent": peak})

    for reason, count in sorted(s["turn_aborts"].items()):
        level, why = ABORT_NOTES.get(reason, ("info", "reason %s" % reason))
        report.add(level, "TURN_ABORTED",
                   "Session %s aborted %d turn(s): %s. Aborted turns produce partial "
                   "evidence, so read the findings above with that in mind."
                   % (sid, count, why), {"reason": reason, "count": count})


def method_session(args: argparse.Namespace) -> Report:
    codex_home = Path(args.codex_home).expanduser()
    report = Report(method="session")

    if not codex_home.is_dir():
        report.add("critical", "NO_CODEX_HOME", "CODEX_HOME not found: %s" % codex_home)
        return report

    cfg = read_config(codex_home)
    registry = ModelRegistry.build(codex_home, cfg, args.model_catalog, args.tier_map)
    registry.apply_notes(report)
    requested = args.model or cfg.get("model")
    provider_id = cfg.get("model_provider")
    providers = cfg.get("model_providers") or {}
    prov = providers.get(provider_id, {}) if provider_id else {}
    base_url = prov.get("base_url")
    endpoint_class = classify_endpoint(base_url)

    report.requested_model = requested
    report.details.update({
        "codex_home": str(codex_home),
        "configured_model": cfg.get("model"),
        "reasoning_effort": cfg.get("model_reasoning_effort"),
        "provider_id": provider_id,
        "endpoint_class": endpoint_class,
        "base_url": base_url,
        "wire_api": prov.get("wire_api"),
        "platform": platform_summary(),
        "model_catalog": registry.describe(),
    })

    if endpoint_class == "third-party":
        report.add("warn", "PROVIDER_THIRD_PARTY",
                   "Traffic goes to a third-party endpoint (%s), not OpenAI. That relay "
                   "controls every routing header and can swap the upstream model, so the "
                   "id fingerprints below are the usable evidence." % base_url,
                   {"provider": provider_id, "base_url": base_url})
    else:
        report.add("ok", "PROVIDER_OFFICIAL",
                   "Provider resolves to an official OpenAI endpoint (%s)." % endpoint_class,
                   {"provider": provider_id, "base_url": base_url})

    rollouts = find_rollouts(codex_home, args.session_id, args.sessions)
    if not rollouts:
        where = args.session_id or "the %d most recent sessions" % args.sessions
        report.add("warn", "NO_ROLLOUT", "No rollout files matched %s under %s."
                   % (where, codex_home / "sessions"))
        return report

    parsed = []
    for path in rollouts:
        try:
            parsed.append(parse_rollout(path))
        except OSError as exc:
            report.add("info", "ROLLOUT_UNREADABLE", "Could not read %s: %s" % (path.name, exc))
    report.details["sessions"] = parsed

    for s in parsed:
        sid = s["session_id"] or "(unknown)"

        for event in s["reroute_events"]:
            if event.get("type") == "safety_buffering":
                report.add("warn", "SAFETY_BUFFERING_APPLIED",
                           "Session %s reported safety buffering." % sid, event)
                continue
            report.add("critical", "REROUTE_EVENT_IN_ROLLOUT",
                       "Session %s recorded a model reroute." % sid, event)
            source, target = event.get("from_model"), event.get("to_model")
            if isinstance(source, str) and source and isinstance(target, str) and target:
                comparison = Report("session", requested_model=source)
                judge_served_model(comparison, source, target,
                                   {"session_id": sid, "event": event}, registry=registry)
                report.findings.extend(comparison.findings)

        fams = [f for f in s["backend_families"] if f != "unknown"]
        if len(fams) > 1:
            report.add("warn", "MIXED_BACKEND_FAMILY",
                       "Session %s returned response ids from more than one backend family "
                       "(%s). Mid-session backend switching is a strong reroute indicator."
                       % (sid, ", ".join(sorted(fams))),
                       s["backend_families"])

        session_models = s["turn_models"] or ([requested] if requested else [])
        identities = [i for i in (registry.identify(m) for m in session_models) if i]
        openai_models = [i.slug for i in identities if i.vendor == "openai"]
        if openai_models and "anthropic-messages" in s["backend_families"]:
            report.add("critical", "VENDOR_MISMATCH",
                       "Session %s requested OpenAI model(s) %s but the server returned "
                       "Anthropic-style response ids. These turns were not served by OpenAI."
                       % (sid, ", ".join(openai_models)),
                       s["backend_families"])

        unrecorded = [i.slug for i in identities if not i.known]
        if unrecorded:
            report.add("warn", "SESSION_MODEL_UNRECORDED",
                       "Session %s ran model(s) %s that appear in neither the built-in "
                       "rank table nor your model catalog (%s). Confirm you chose them."
                       % (sid, ", ".join(unrecorded),
                          registry.catalog_path or "no catalog loaded"),
                       {"unrecorded_models": unrecorded,
                        "inferred": [{"slug": i.slug, "vendor": i.vendor,
                                      "version": list(i.version),
                                      "size_marker": i.size_marker} for i in identities
                                     if not i.known]})

        judge_session_headers(report, s, sid, endpoint_class)

        expected_windows = {i.context_window for i in identities if i.context_window}
        for window in s["context_windows"]:
            if not expected_windows or window in expected_windows:
                continue
            named = {i.normalized for i in identities}
            owners = [o for o in registry.window_owners(window) if o not in named]
            if not owners:
                continue
            report.add("info", "CONTEXT_WINDOW_HINT",
                       "Session %s reported a %d-token context window: not the catalogued "
                       "window for %s, but the window of %s. A lead on what really served "
                       "the turn, not proof."
                       % (sid, window, ", ".join(i.slug for i in identities),
                          ", ".join(owners[:5]) + (", and others" if len(owners) > 5 else "")),
                       {"reported_window": window, "candidates": owners[:20]})

        if len(s["turn_models"]) > 1:
            report.add("info", "MULTIPLE_TURN_MODELS",
                       "Session %s recorded more than one requested model (%s). Sub-agent "
                       "and review turns do this legitimately."
                       % (sid, ", ".join(s["turn_models"])),
                       s["turn_models"])

        judge_session_settings(report, s, sid)

    if not args.no_log_scan:
        scan_logs(codex_home, args.log_hours, report)
    else:
        report.add("warn", "LOGSCAN_SKIPPED",
                   "The log database was not scanned. Routing evidence available only in "
                   "that database was not checked.")

    return report



# ---------------------------------------------------------------------------
# Shared active probe used by methods 2 and 3
# ---------------------------------------------------------------------------
# Failure classes named after the codexErrorInfo variants Codex reports for its
# own turns. Entries are (action, safe to retry automatically, guidance).
ERROR_ACTIONS: Dict[str, Tuple[str, bool, str]] = {
    "unauthorized": (
        "manualReview", False,
        "Repair authentication first. An identical resubmission cannot fix credentials."),
    "usageLimitExceeded": (
        "manualReview", False,
        "Wait for the account-level reset. Retrying sooner only burns more quota."),
    "cyberPolicy": (
        "manualReview", False,
        "A typed policy refusal. Do not rephrase the request to work around it."),
    "clientRateLimited": (
        "retryable", True,
        "Your own request rate ramped too quickly. Back off, then retry unchanged."),
    "serverOverloaded": (
        "retryable", True,
        "Transient capacity trouble on the server. Bounded backoff is the right response."),
    "internalServerError": (
        "retryable", True,
        "Server-side fault. Retry a bounded number of times before drawing conclusions."),
    "httpConnectionFailed": (
        "retryable", True,
        "Transport-level failure before any response arrived. Check the network path."),
    "responseStreamDisconnected": (
        "retryable", True,
        "The stream ended without completing. Resubmit the same request."),
    "requestTimeout": (
        "retryable", True,
        "No response inside the timeout budget. Retry, or raise --timeout."),
    "contextWindowExceeded": (
        "recreate", False,
        "Shorten the probe prompt rather than repeating this request."),
    "badRequest": (
        "recreate", False,
        "The request itself is wrong. Change the model slug or the payload."),
    "modelNotAvailable": (
        "recreate", False,
        "The backend refuses this model outright. Outright denial is the honest failure "
        "mode; the dishonest one is being handed a cheaper model instead."),
    "other": (
        "manualReview", False,
        "Unrecognised failure. Observe it before automating anything around it."),
}


def classify_backend_error(status: Optional[int], body: str,
                           headers: Optional[Dict[str, str]] = None,
                           transport_reason: Any = None) -> Dict[str, Any]:
    """Map one probe failure onto Codex's own error vocabulary, separating 'the
    model was refused' from 'the connection wobbled'. Only the first is evidence
    about routing; only the second is worth retrying."""
    text = (body or "").lower()
    headers = headers or {}
    info = "other"

    if transport_reason is not None:
        reason = str(transport_reason).lower()
        info = "requestTimeout" if ("timed out" in reason or "timeout" in reason) \
            else "httpConnectionFailed"
    elif status == 401:
        info = "unauthorized"
    elif status == 403:
        info = "cyberPolicy" if ("policy" in text or "violat" in text) else "unauthorized"
    elif status == 404:
        info = "modelNotAvailable" if "model" in text else "badRequest"
    elif status == 429:
        if "slow_down" in text:
            info = "clientRateLimited"
        elif "cooldown" in text:
            info = "modelNotAvailable"
        else:
            info = "usageLimitExceeded"
    elif status in (400, 422):
        if "context" in text and ("length" in text or "window" in text):
            info = "contextWindowExceeded"
        elif "model" in text and any(t in text for t in
                                     ("not found", "does not exist", "unsupported",
                                      "invalid", "unavailable", "no access")):
            info = "modelNotAvailable"
        elif "policy" in text:
            info = "cyberPolicy"
        else:
            info = "badRequest"
    elif status in (502, 503, 504) or "server_is_overloaded" in text:
        info = "serverOverloaded"
    elif status is not None and 500 <= status < 600:
        info = "internalServerError"
    elif status is not None and 400 <= status < 500:
        info = "badRequest"

    # Quota language beats the status code: some gateways report exhaustion as
    # a plain 400 or 500.
    if any(t in text for t in ("usage_limit", "usagelimit", "quota", "insufficient_quota",
                               "credit", "billing")):
        info = "usageLimitExceeded"

    action, automatic, guidance = ERROR_ACTIONS.get(info, ERROR_ACTIONS["other"])
    retry_after = None
    raw = headers.get("retry-after")
    if raw:
        try:
            retry_after = max(0.0, min(60.0, float(str(raw).strip())))
        except ValueError:
            retry_after = None

    return {
        "error_info": info,
        "action": action,
        "automatic": automatic,
        "guidance": guidance,
        "status": status,
        "retry_after": retry_after,
        "transport_reason": str(transport_reason) if transport_reason is not None else None,
    }


def _error_headline(err: Dict[str, Any], result: Dict[str, Any]) -> str:
    if err.get("status"):
        head = "The endpoint returned HTTP %s." % err["status"]
    elif err.get("transport_reason"):
        head = "The request never completed (%s)." % err["transport_reason"]
    else:
        head = "The request failed."
    if result.get("stream_error"):
        head += " The stream reported: %s" % str(result["stream_error"])[:200]
    return head


def _probe_once(url: str, headers: Dict[str, str], payload: bytes, timeout: float,
                insecure: bool, ca_bundle: Optional[str]) -> Dict[str, Any]:
    """One request. Gathers evidence and never raises; the caller decides what
    the outcome means and whether another attempt is warranted."""
    out: Dict[str, Any] = {
        "status": None, "raw_headers": {}, "served_model": None, "engine_ids": [],
        "safety_buffering": None, "body": "", "stream_error": None,
        "stream_completed": False, "error": None, "elapsed_s": 0.0,
    }
    started = time.monotonic()

    try:
        ctx = make_ssl_context(insecure, ca_bundle)
    except Exception as exc:  # noqa: BLE001
        out["error"] = classify_backend_error(None, "", {}, "--ca-bundle unusable: %s" % exc)
        out["error"]["automatic"] = False
        return out

    request = urllib.request.Request(url, data=payload, method="POST")
    for key, value in headers.items():
        request.add_header(key, value)

    response = None
    try:
        response = urllib.request.urlopen(request, timeout=timeout, context=ctx)
    except urllib.error.HTTPError as exc:
        # A 4xx or 5xx still carries the routing and quota headers, and that is
        # frequently the exact moment a downgrade is being applied.
        out["status"] = exc.code
        out["raw_headers"] = {k.lower(): v for k, v in exc.headers.items()}
        try:
            out["body"] = exc.read(4096).decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            pass
        out["error"] = classify_backend_error(exc.code, out["body"], out["raw_headers"])
        out["elapsed_s"] = round(time.monotonic() - started, 2)
        return out
    except urllib.error.URLError as exc:
        out["error"] = classify_backend_error(None, "", {}, exc.reason)
        out["elapsed_s"] = round(time.monotonic() - started, 2)
        return out
    except Exception as exc:  # noqa: BLE001
        out["error"] = classify_backend_error(None, "", {}, exc)
        out["elapsed_s"] = round(time.monotonic() - started, 2)
        return out

    try:
        with response:
            out["status"] = response.status
            observed = {k.lower(): v for k, v in response.headers.items()}
            out["raw_headers"] = observed
            out["served_model"] = observed.get("openai-model") or observed.get("x-openai-model")

            deadline = time.monotonic() + timeout
            for raw_line in response:
                if time.monotonic() > deadline:
                    out["stream_error"] = "timed out while reading the stream"
                    break
                line = raw_line.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                chunk = line[5:].strip()
                if chunk == "[DONE]":
                    out["stream_completed"] = True
                    break

                for match in re.finditer(r'"engine_ids?"\s*:\s*"([^"]+)"', chunk):
                    out["engine_ids"].append(match.group(1))

                try:
                    event = json.loads(chunk)
                except Exception:  # noqa: BLE001
                    continue

                inner = event.get("response") or {}
                if not out["served_model"] and isinstance(inner, dict) and inner.get("model"):
                    out["served_model"] = str(inner["model"])

                if event.get("safety_buffering"):
                    out["safety_buffering"] = event["safety_buffering"]
                meta = event.get("metadata")
                if isinstance(meta, dict):
                    if meta.get("type") == "safety_buffering":
                        out["safety_buffering"] = meta
                    for header in meta.get("headers") or []:
                        if isinstance(header, dict):
                            name = str(header.get("name", "")).lower()
                            if name in ("openai-model", "x-openai-model") and header.get("value"):
                                out["served_model"] = out["served_model"] or str(header["value"])

                kind = event.get("type")
                if kind in ("error", "response.failed", "response.incomplete"):
                    detail = event.get("error") or (inner.get("error") if isinstance(inner, dict) else None) or event
                    out["stream_error"] = json.dumps(detail, ensure_ascii=False, default=str)[:600]
                    out["error"] = classify_backend_error(out["status"], out["stream_error"],
                                                          observed)
                    break
                if kind == "response.completed":
                    out["stream_completed"] = True
                    break
    except Exception as exc:  # noqa: BLE001
        # Headers already arrived; only the stream broke.
        out["stream_error"] = str(exc)
        out["error"] = out["error"] or classify_backend_error(
            out["status"], "", out["raw_headers"], "stream failed: %s" % exc)

    if (out["error"] is None and not out["stream_completed"]
            and not out["served_model"] and out["status"] and out["status"] < 400):
        action, automatic, guidance = ERROR_ACTIONS["responseStreamDisconnected"]
        out["error"] = {
            "error_info": "responseStreamDisconnected", "action": action,
            "automatic": automatic, "guidance": guidance, "status": out["status"],
            "retry_after": None,
            "transport_reason": "the stream ended without completing and without naming a model",
        }

    out["elapsed_s"] = round(time.monotonic() - started, 2)
    return out


def probe_responses(url: str, headers: Dict[str, str], model: str, prompt: str,
                    timeout: float, insecure: bool, report: Report,
                    retries: int = 2, ca_bundle: Optional[str] = None) -> Dict[str, Any]:
    """Send a minimal streaming Responses request and harvest routing evidence.
    Only failure classes Codex itself treats as automatically retryable get
    another attempt; auth, quota and policy failures never do."""
    payload = json.dumps({
        "model": model,
        "input": [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
        "store": False,
        "stream": True,
    }).encode("utf-8")

    attempts: List[Dict[str, Any]] = []
    budget = max(1, int(retries) + 1)
    result: Dict[str, Any] = {}

    for attempt in range(1, budget + 1):
        result = _probe_once(url, headers, payload, timeout, insecure, ca_bundle)
        err = result.get("error")
        attempts.append({"attempt": attempt, "status": result.get("status"),
                         "error_info": (err or {}).get("error_info"),
                         "elapsed_s": result.get("elapsed_s")})
        if not err or not err.get("automatic") or attempt >= budget:
            break
        delay = err.get("retry_after")
        if delay is None:
            delay = min(8.0, 0.75 * (2 ** (attempt - 1)))
        delay += random.uniform(0.0, 0.25)
        report.add("info", "PROBE_RETRY",
                   "Attempt %d of %d hit '%s', which Codex classes as automatically "
                   "retryable. Waiting %.1fs, then trying again."
                   % (attempt, budget, err["error_info"], delay),
                   {"attempt": attempt, "classification": err})
        time.sleep(delay)

    observed = result.get("raw_headers") or {}
    interesting = {k: observed[k] for k in HEADERS_OF_INTEREST if k in observed}
    err = result.get("error")

    if err:
        level = {"retryable": "warn", "recreate": "critical",
                 "manualReview": "critical"}.get(err["action"], "warn")
        report.add(level, "BACKEND_ERROR",
                   "%s Codex classes this as '%s' (recovery action: %s; safe to retry "
                   "automatically: %s). %s"
                   % (_error_headline(err, result), err["error_info"], err["action"],
                      "yes" if err["automatic"] else "no", err["guidance"]),
                   {"classification": err, "attempts": attempts,
                    "body": (result.get("body") or "")[:600],
                    "stream_error": result.get("stream_error")})

        if err["error_info"] in ("usageLimitExceeded", "modelNotAvailable"):
            report.add("critical", "MODEL_UNAVAILABLE",
                       "This model is being refused rather than served (%s). Refusal is the "
                       "honest failure; the dishonest one is a quiet substitution, so re-run "
                       "this check once capacity returns and compare the served model."
                       % err["error_info"],
                       {"status": result.get("status"),
                        "body": (result.get("body") or "")[:600]})
        if err["error_info"] == "unauthorized":
            report.add("warn", "AUTH_EXPIRED",
                       "The backend rejected the credentials. On a ChatGPT install the "
                       "access token has usually just expired: open Codex once so it "
                       "refreshes, then re-run. Resubmitting unchanged cannot repair this.")
        if err["error_info"] == "cyberPolicy":
            report.add("warn", "POLICY_REFUSAL",
                       "The backend refused this request on policy grounds. That is a "
                       "decision to review by hand, not something to rephrase around, and "
                       "it says nothing about which model you were given.")

    if len(attempts) > 1:
        report.add("info", "PROBE_ATTEMPTS",
                   "The probe needed %d attempts before settling." % len(attempts), attempts)

    if result.get("safety_buffering"):
        report.add("warn", "SAFETY_BUFFERING_APPLIED",
                   "The stream reported safety buffering. Use the serving model or an "
                   "explicit reroute event to identify a model change.", result["safety_buffering"])
    if result.get("engine_ids"):
        unique = sorted(set(result["engine_ids"]))
        report.add("info", "ENGINE_IDS",
                   "Server timing metrics exposed engine ids: %s. Compare the family prefix "
                   "against the model you selected." % ", ".join(unique), unique)

    return {
        "status": result.get("status"),
        "headers": interesting,
        "all_header_names": sorted(observed),
        "served_model": result.get("served_model"),
        "engine_ids": sorted(set(result.get("engine_ids") or [])),
        "safety_buffering": result.get("safety_buffering"),
        "stream_completed": result.get("stream_completed"),
        "classification": err,
        "attempts": attempts,
        "elapsed_s": result.get("elapsed_s", 0.0),
    }



# ---------------------------------------------------------------------------
# METHOD 2 -- official ChatGPT Codex backend via auth.json
# ---------------------------------------------------------------------------
DEFAULT_OFFICIAL_BASE = "https://chatgpt.com/backend-api/codex"


def method_official(args: argparse.Namespace) -> Report:
    report = Report(method="official")

    codex_home = Path(args.codex_home).expanduser()
    auth_path = Path(args.auth_file).expanduser() if args.auth_file else codex_home / "auth.json"
    if not auth_path.is_file():
        report.add("critical", "NO_AUTH_FILE",
                   "auth.json not found at %s. Sign in with Codex first, or pass "
                   "--auth-file." % auth_path)
        return report

    try:
        auth = json.loads(auth_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        report.add("critical", "AUTH_UNREADABLE", "Could not parse %s: %s" % (auth_path, exc))
        return report

    tokens = auth.get("tokens") or {}
    access_token = tokens.get("access_token")
    account_id = args.account_id or tokens.get("account_id")
    if not access_token:
        report.add("critical", "NO_ACCESS_TOKEN",
                   "%s has no tokens.access_token, so this install is not signed in "
                   "with ChatGPT credentials." % auth_path)
        return report

    cfg = read_config(codex_home) if codex_home.is_dir() else {}
    registry = ModelRegistry.build(codex_home if codex_home.is_dir() else None, cfg,
                                   args.model_catalog, args.tier_map)
    registry.apply_notes(report)
    report.details["model_catalog"] = registry.describe()
    model = args.model or cfg.get("model")
    if not model:
        report.add("critical", "NO_MODEL",
                   "No model given and none configured. Pass --model gpt-5.6-sol.")
        return report
    identity = registry.identify(model)
    if identity and identity.vendor != "openai":
        report.add("warn", "NON_OPENAI_MODEL",
                   "'%s' is not an OpenAI first-party slug, so the official backend will "
                   "almost certainly reject it." % model)
    elif identity and not identity.known:
        report.add("info", "MODEL_UNRECORDED_REQUEST",
                   "'%s' is ranked nowhere local (%s); it may simply be newer than the "
                   "catalog, so the backend's own answer below is the authority."
                   % (model, registry.catalog_path or "none loaded"))

    base_url = args.base_url or DEFAULT_OFFICIAL_BASE
    url = base_url.rstrip("/") + args.path

    headers = {
        "authorization": "Bearer %s" % access_token,
        "content-type": "application/json",
        "accept": "text/event-stream",
        "originator": args.originator,
        "session_id": str(uuid.uuid4()),
        "x-responsesapi-include-timing-metrics": "true",
    }
    if account_id:
        headers["chatgpt-account-id"] = account_id
    for item in args.header or []:
        if "=" in item:
            k, v = item.split("=", 1)
            headers[k.strip().lower()] = v.strip()

    report.requested_model = model
    report.details.update({
        "url": url,
        "auth_file": str(auth_path),
        "auth_mode": auth.get("auth_mode"),
        "account_id_present": bool(account_id),
        "last_refresh": auth.get("last_refresh"),
        "platform": platform_summary(),
    })

    result = probe_responses(url, headers, model, args.prompt, args.timeout,
                             args.insecure, report, retries=args.retries,
                             ca_bundle=args.ca_bundle)
    report.details["probe"] = result

    judge_served_model(report, model, result["served_model"], result["headers"],
                       status=result["status"], registry=registry)
    judge_headers(report, result["headers"])
    judge_required_headers(report, result["headers"], classify_endpoint(base_url),
                           bool(result["status"]) and result["status"] < 400)
    return report



# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
COLORS = {"critical": "\033[31m", "warn": "\033[33m", "ok": "\033[32m", "info": "\033[90m"}
RESET = "\033[0m"


def supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    if not sys.stdout.isatty():
        return False
    if not IS_WINDOWS and os.environ.get("TERM", "").lower() == "dumb":
        return False
    return enable_ansi()


def render(report: Report, show_evidence: bool) -> None:
    verdict, _ = report.verdict
    color = supports_color()
    bar = "-" * 78

    print()
    print("Codex downgrade check  [method: %s]" % report.method)
    print(bar)
    if report.requested_model:
        print("  requested model : %s" % report.requested_model)
    if report.served_model:
        print("  served model    : %s" % report.served_model)
    for key in ("endpoint_class", "base_url", "url", "provider_id", "provider",
                "reasoning_effort", "auth", "auth_file", "codex_home"):
        if report.details.get(key):
            print("  %-15s : %s" % (key, report.details[key]))
    catalog = report.details.get("model_catalog") or {}
    if catalog.get("catalog_path"):
        print("  %-15s : %s (%d models)"
              % ("model catalog", catalog["catalog_path"], catalog["catalog_models"]))

    probe = report.details.get("probe")
    if probe:
        print("  http status     : %s" % probe.get("status"))
        print("  elapsed         : %ss" % probe.get("elapsed_s"))
        if probe.get("headers"):
            print(bar)
            print("  routing headers:")
            for k, v in sorted(probe["headers"].items()):
                print("    %-42s %s" % (k, v))

    sessions = report.details.get("sessions")
    if sessions:
        print(bar)
        for s in sessions:
            fams = ", ".join("%s x%d" % (k, v) for k, v in sorted(s["backend_families"].items())) or "none recorded"
            print("  session %s" % (s["session_id"] or "(unknown)"))
            print("    turn models     : %s" % (", ".join(s["turn_models"]) or "-"))
            print("    backend ids     : %s" % fams)
            if s["settings_models"]:
                print("    settings models : %s" % ", ".join(s["settings_models"]))
            if s["settings_providers"]:
                print("    providers       : %s" % ", ".join(s["settings_providers"]))
            print("    quota snapshots : %d populated of %d"
                  % (s["rate_snapshots_populated"], s["rate_snapshots_total"]))
            if s["peak_used_percent"]:
                print("    peak window use : %s%%" % s["peak_used_percent"])
            if s["turn_aborts"]:
                print("    aborted turns   : %s"
                      % ", ".join("%s x%d" % kv for kv in sorted(s["turn_aborts"].items())))

    print(bar)
    for f in report.findings:
        tag = "[%s] %s" % (f.level.upper(), f.code)
        if color:
            tag = COLORS.get(f.level, "") + tag + RESET
        print("  " + tag)
        for chunk in wrap(f.message, 74):
            print("        " + chunk)
        if show_evidence and f.evidence not in (None, "", [], {}):
            ev = json.dumps(f.evidence, ensure_ascii=False, default=str)
            print("        evidence: %s" % ev[:600])

    print(bar)
    vtag = "  VERDICT: %s" % verdict
    if color:
        _, exit_code = report.verdict
        c = COLORS["critical"] if exit_code == 3 else (COLORS["warn"] if exit_code == 2 else COLORS["ok"])
        vtag = c + vtag + RESET
    print(vtag)
    print()


def wrap(text: str, width: int) -> List[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines or [""]


# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------
# A finished report is worth sharing; the machine it came from is not. --redact
# strips the parts that identify you and keeps the parts that identify the
# downgrade.
_UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
_URL_HOST_RE = re.compile(r"(https?://)([^/\s\"']+)")


# Stock provider aliases name a vendor, not a person, and several are
# substrings of terms the report needs to keep readable ("openai-responses").
GENERIC_PROVIDER_ALIASES = frozenset({
    "openai", "azure", "openrouter", "ollama", "anthropic", "google", "gemini",
    "mistral", "groq", "deepseek", "qwen", "vertex", "bedrock", "local", "oss",
})


def redaction_terms() -> List[str]:
    """Values that name the machine or the account rather than the finding.
    Longest first, so a home directory is replaced before the username inside it."""
    terms = []
    home = os.path.expanduser("~")
    if home and home not in ("~", "/", ""):
        terms.append(home)
        terms.append(Path(home).name)
    for name in ("USERNAME", "USER", "LOGNAME", "COMPUTERNAME", "HOSTNAME"):
        value = os.environ.get(name)
        if value:
            terms.append(value)
    return sorted({t for t in terms if t and len(t) > 2}, key=len, reverse=True)


def redact_string(text: str, terms: Iterable[str]) -> str:
    for term in terms:
        text = text.replace(term, "<redacted>")
    text = _URL_HOST_RE.sub(lambda m: m.group(1) + "<host>", text)
    return _UUID_RE.sub("<uuid>", text)


def redact(value: Any, terms: List[str]) -> Any:
    if isinstance(value, str):
        return redact_string(value, terms)
    if isinstance(value, dict):
        return {k: redact(v, terms) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v, terms) for v in value]
    if isinstance(value, tuple):
        return tuple(redact(v, terms) for v in value)
    return value


def apply_redaction(report: Report) -> None:
    terms = redaction_terms()
    # Provider aliases are chosen by the user, so they identify the setup too.
    aliases = [report.details.get(key) for key in ("provider_id", "provider")]
    for session in report.details.get("sessions") or []:
        if isinstance(session, dict):
            aliases.append(session.get("session_provider"))
            aliases.extend(session.get("settings_providers") or [])
    for alias in aliases:
        if (isinstance(alias, str) and len(alias) > 2
                and alias.lower() not in GENERIC_PROVIDER_ALIASES):
            terms.append(alias)
    terms = sorted(set(terms), key=len, reverse=True)
    report.details = redact(report.details, terms)
    report.findings = [
        Finding(f.level, f.code, redact_string(f.message, terms), redact(f.evidence, terms))
        for f in report.findings
    ]



# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
EPILOG = """
examples
  python codex_downgrade.py session  --session-id 0199c2f4-1a2b-7c3d-8e4f-5a6b7c8d9e0f
  python codex_downgrade.py session  --sessions 10 --json
  python codex_downgrade.py official --model gpt-6-astra --redact
  python codex_downgrade.py official --model gpt-6.1-sol --tier-map ranks.json

exit codes
  0 clean   2 at risk or incomplete   3 model changed, rerouted or unavailable   1 tool error

README.md documents every parameter, every finding code, and where each signal
comes from.
"""


def _common_flags() -> argparse.ArgumentParser:
    # SUPPRESS stops the subparser copy clobbering a value given before it.
    c = argparse.ArgumentParser(add_help=False)
    c.add_argument("--json", action="store_true", default=argparse.SUPPRESS,
                   help="Emit a JSON report instead of text.")
    c.add_argument("--evidence", action="store_true", default=argparse.SUPPRESS,
                   help="Show the raw evidence blob under each finding.")
    c.add_argument("--redact", action="store_true", default=argparse.SUPPRESS,
                   help="Mask paths, usernames, hostnames and session UUIDs.")
    return c


def _model_source_flags() -> argparse.ArgumentParser:
    m = argparse.ArgumentParser(add_help=False)
    m.add_argument("--model-catalog", default=None, metavar="PATH",
                   help="Model catalog JSON, i.e. models_cache.json. Default: the "
                        "path in config.toml, else $CODEX_HOME/models_cache.json.")
    m.add_argument("--tier-map", default=None, metavar="PATH",
                   help="JSON object mapping model slug to integer rank, higher "
                        "meaning a higher audit tier. Overrides built-in ranks.")
    return m


def build_parser() -> argparse.ArgumentParser:
    common = _common_flags()
    msrc = _model_source_flags()
    p = argparse.ArgumentParser(
        prog="codex_downgrade.py",
        description="Detect whether Codex is being served by a lower-tier model than selected.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--json", action="store_true",
                   help="Emit a JSON report instead of text.")
    p.add_argument("--evidence", action="store_true",
                   help="Show the raw evidence blob under each finding.")
    p.add_argument("--redact", action="store_true",
                   help="Mask paths, usernames, hostnames and session UUIDs.")
    sub = p.add_subparsers(dest="method", required=True)

    s = sub.add_parser(
        "session", parents=[common, msrc],
        help="Method 1: offline audit of a local Codex session.",
        description="Audits session rollouts and the local log database already on "
                    "disk. Needs no network and no credentials.")
    s.add_argument("--session-id", default=None,
                   help="Session UUID to audit; a unique prefix also works. Omit to "
                        "audit the most recently modified sessions.")
    s.add_argument("--sessions", type=int, default=3, metavar="N",
                   help="Audit the N most recent sessions. Default: 3.")
    s.add_argument("--codex-home", default=str(default_codex_home()), metavar="DIR",
                   help="Codex state directory. Default: $CODEX_HOME or ~/.codex.")
    s.add_argument("--model", default=None, metavar="SLUG",
                   help="Model you believe you selected. Overrides config.toml.")
    s.add_argument("--no-log-scan", action="store_true",
                   help="Skip the logs_*.sqlite scan.")
    s.add_argument("--log-hours", type=int, default=168, metavar="H",
                   help="How far back to scan the log database. Default: 168.")
    s.set_defaults(func=method_session)

    o = sub.add_parser(
        "official", parents=[common, msrc],
        help="Method 2: probe the official Codex backend using auth.json.",
        description="Sends one minimal streaming request to the official ChatGPT Codex "
                    "backend using your local credentials, then reads the real routing "
                    "and quota headers.")
    o.add_argument("--model", default=None, metavar="SLUG",
                   help="OpenAI model slug to request. Defaults to config.toml's model.")
    o.add_argument("--codex-home", default=str(default_codex_home()), metavar="DIR",
                   help="Codex state directory. Default: $CODEX_HOME or ~/.codex.")
    o.add_argument("--auth-file", default=None, metavar="FILE",
                   help="Explicit auth.json path. Overrides --codex-home.")
    o.add_argument("--account-id", default=None, metavar="ID",
                   help="Override the chatgpt-account-id header.")
    o.add_argument("--base-url", default=DEFAULT_OFFICIAL_BASE, metavar="URL",
                   help="Official backend root. Default: " + DEFAULT_OFFICIAL_BASE + ".")
    o.add_argument("--path", default="/responses", metavar="PATH",
                   help="Path appended to --base-url. Default: /responses.")
    o.add_argument("--prompt", default="ping", metavar="TEXT",
                   help="Probe prompt body. Default: ping.")
    o.add_argument("--header", action="append", metavar="K=V",
                   help="Extra request header, repeatable.")
    o.add_argument("--originator", default="codex_cli_rs", metavar="NAME",
                   help="Originator header value. Default: codex_cli_rs.")
    o.add_argument("--timeout", type=float, default=60.0, metavar="SECONDS",
                   help="Connect plus stream-read budget. Default: 60.")
    o.add_argument("--insecure", action="store_true",
                   help="Skip TLS verification. Should never be needed here.")
    o.add_argument("--ca-bundle", default=None, metavar="PATH",
                   help="PEM roots for a corporate TLS proxy. Preferred over --insecure.")
    o.add_argument("--retries", type=int, default=2, metavar="N",
                   help="Extra attempts, retryable failure classes only. Auth, quota "
                        "and policy failures are never retried. Default: 2.")
    o.set_defaults(func=method_official)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    configure_stdout()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        report = args.func(args)
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 1
    finally:
        cleanup_temp_copies()

    if getattr(args, "redact", False):
        apply_redaction(report)

    verdict, code = report.verdict
    want_json = getattr(args, "json", False)
    want_evidence = getattr(args, "evidence", False)
    if want_json:
        payload = {
            "method": report.method,
            "verdict": verdict,
            "exit_code": code,
            "requested_model": report.requested_model,
            "served_model": report.served_model,
            "details": report.details,
            "findings": [asdict(f) for f in report.findings],
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
    else:
        render(report, want_evidence)
    return code


if __name__ == "__main__":
    sys.exit(main())

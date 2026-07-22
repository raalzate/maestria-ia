import json
import os
import shutil
from typing import Any

# When packaged as a desktop app the bundle is read-only, so all user data must
# live under a writable per-user directory. The desktop bootstrap exports
# DDD_STUDIO_DATA_DIR; when it is unset (dev mode) we keep the original
# CWD-relative layout so nothing changes for `streamlit run` / tests.
_DATA_ROOT = os.environ.get("DDD_STUDIO_DATA_DIR")

if _DATA_ROOT:
    STATIC_DIR = os.path.join(_DATA_ROOT, "static")
    CACHE_DIR = os.path.join(_DATA_ROOT, ".cache")
else:
    STATIC_DIR = "static"
    CACHE_DIR = ".cache"

STATIC_JSON_PATH = os.path.join(STATIC_DIR, "domain_analysis.json")
LLM_CONFIG_PATH = os.path.join(STATIC_DIR, "llm_config.json")


def save_static_json(data: dict):
    """Guarda el JSON en disco para persistencia."""
    os.makedirs(STATIC_DIR, exist_ok=True)
    with open(STATIC_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_static_json() -> dict[str, Any]:
    """Carga el JSON persistido si existe."""
    if os.path.exists(STATIC_JSON_PATH):
        try:
            with open(STATIC_JSON_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_llm_config(config: dict) -> None:
    """Persist LLM configuration to disk."""
    os.makedirs(STATIC_DIR, exist_ok=True)
    with open(LLM_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def load_llm_config() -> dict | None:
    """Load persisted LLM configuration from disk, or None if not found."""
    if os.path.exists(LLM_CONFIG_PATH):
        try:
            with open(LLM_CONFIG_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def clear_static_json():
    """Elimina el archivo JSON estático."""
    if os.path.exists(STATIC_JSON_PATH):
        os.remove(STATIC_JSON_PATH)


def clear_cache_dir(cache_dir: str | None = None) -> int:
    """Remove all files inside the cache directory. Returns count removed."""
    path = cache_dir or CACHE_DIR
    if not os.path.isdir(path):
        return 0
    removed = 0
    for name in os.listdir(path):
        target = os.path.join(path, name)
        try:
            if os.path.isfile(target) or os.path.islink(target):
                os.remove(target)
                removed += 1
            elif os.path.isdir(target):
                shutil.rmtree(target)
                removed += 1
        except OSError:
            pass
    return removed


def clear_drafts_dir(drafts_dir: str | None = None) -> int:
    """Remove all drafts and the manifest. Returns count removed."""
    path = drafts_dir or DRAFTS_DIR
    if not os.path.isdir(path):
        return 0
    removed = 0
    for name in os.listdir(path):
        target = os.path.join(path, name)
        try:
            if os.path.isfile(target) or os.path.islink(target):
                os.remove(target)
                removed += 1
            elif os.path.isdir(target):
                shutil.rmtree(target)
                removed += 1
        except OSError:
            pass
    return removed


def clear_llm_config() -> None:
    """Remove persisted LLM configuration (API key + model)."""
    if os.path.exists(LLM_CONFIG_PATH):
        os.remove(LLM_CONFIG_PATH)


def clear_all_data(include_llm_config: bool = False) -> dict[str, int]:
    """Full wipe: static analysis, cache, drafts. Optionally llm_config.

    Returns counts per category.
    """
    counts = {
        "static": 0,
        "cache": 0,
        "drafts": 0,
        "llm_config": 0,
    }
    if os.path.exists(STATIC_JSON_PATH):
        os.remove(STATIC_JSON_PATH)
        counts["static"] = 1
    counts["cache"] = clear_cache_dir()
    counts["drafts"] = clear_drafts_dir()
    if include_llm_config and os.path.exists(LLM_CONFIG_PATH):
        os.remove(LLM_CONFIG_PATH)
        counts["llm_config"] = 1
    return counts


# ── Drafts directory management ──────────────────────────────────────────

DRAFTS_DIR = os.path.join(os.path.dirname(STATIC_DIR), "drafts")


def ensure_drafts_dir(drafts_dir: str | None = None) -> str:
    """Ensure the drafts directory exists and return its path."""
    path = drafts_dir or DRAFTS_DIR
    os.makedirs(path, exist_ok=True)
    return path


def get_manifest_path(drafts_dir: str | None = None) -> str:
    """Return the path to manifest.json within the drafts directory."""
    path = drafts_dir or DRAFTS_DIR
    return os.path.join(path, "manifest.json")


def seed_user_data(bundle_static_dir: str) -> None:
    """Copy seed files (domain_analysis.json, llm_config.json) from the bundled
    read-only static dir into the writable user data dir if they are missing.

    Called once on first launch of the packaged desktop app. No-op in dev mode
    (when STATIC_DIR is the relative project path the seeds already live there).
    """
    if not bundle_static_dir or os.path.abspath(bundle_static_dir) == os.path.abspath(STATIC_DIR):
        return
    os.makedirs(STATIC_DIR, exist_ok=True)
    for name in ("domain_analysis.json", "llm_config.json"):
        src = os.path.join(bundle_static_dir, name)
        dst = os.path.join(STATIC_DIR, name)
        if os.path.exists(src) and not os.path.exists(dst):
            try:
                shutil.copyfile(src, dst)
            except OSError:
                pass

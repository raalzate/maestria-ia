# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the DDD Studio desktop bundle.

Build (from the project root):
    pyinstaller packaging/ddd_studio.spec --noconfirm --clean

Produces a ONEDIR bundle (and a .app on macOS). Onedir, not onefile: the native
deps (ctranslate2, pyarrow, PyMuPDF, onnxruntime) are heavy, and onefile would
unpack hundreds of MB to a temp dir on every launch and trips Windows AV.
"""

import os
import sys

from PyInstaller.utils.hooks import collect_all, collect_data_files, copy_metadata

# SPECPATH is injected by PyInstaller and is ALREADY the directory containing
# this spec file (packaging/), not the spec file path.
PKG_DIR = SPECPATH  # noqa: F821  (packaging/)
PROJECT_ROOT = os.path.dirname(PKG_DIR)
SRC_ROOT = os.path.join(PROJECT_ROOT, "src")

datas = []
binaries = []
hiddenimports = []

# --- Packages that ship data files / dynamically-imported submodules ---------
_COLLECT = [
    "streamlit",
    "altair",
    "pyarrow",
    "ctranslate2",
    "faster_whisper",
    "av",
    "onnxruntime",
    "langchain",
    "langchain_core",
    "langchain_community",
    "langchain_google_genai",
    "langgraph",
    "anthropic",
    "tokenizers",
    "tiktoken",
    "pydantic",
    "pydantic_core",
    "streamlit_agraph",
]
for pkg in _COLLECT:
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

# --- importlib.metadata version lookups --------------------------------------
# Streamlit (and several deps) call importlib.metadata.version(...) at import.
# A frozen app lacks dist-info by default -> PackageNotFoundError. copy_metadata
# bundles the dist-info so the lookups succeed. This is the #1 Streamlit-under-
# PyInstaller failure mode.
_METADATA = [
    "streamlit",
    "altair",
    "pyarrow",
    "pandas",
    "numpy",
    "click",
    "rich",
    "blinker",
    "tornado",
    "tenacity",
    "packaging",
    "protobuf",
    "anthropic",
    "langchain-core",
    "langchain-community",
    "langgraph",
    "faster-whisper",
    "ctranslate2",
    "pymupdf4llm",
    "pymupdf",
    "graphviz",
    "py2puml",
    "google-cloud-speech",
    "google-generativeai",
    "typing-extensions",
    "gitpython",
    "pympler",
    "validators",
    "watchdog",
    "toml",
]
for dist in _METADATA:
    try:
        datas += copy_metadata(dist)
    except Exception:
        pass

# --- PyMuPDF (fitz) C extension + data ---------------------------------------
try:
    datas += collect_data_files("fitz", include_py_files=False)
except Exception:
    pass
hiddenimports += ["fitz", "pymupdf", "pymupdf4llm"]

# --- google grpc / protobuf hidden imports -----------------------------------
hiddenimports += [
    "google.cloud.speech",
    "google.cloud.speech_v1",
    "grpc",
    "grpc._cython",
    "google.protobuf",
]

# --- our own package: bundle the whole src tree so mixed-root imports resolve -
datas += [(SRC_ROOT, "src")]

# --- bundled relocatable Graphviz (dot + dylibs + plugin subdir) -------------
# Collected by packaging/collect_graphviz.sh. Walk recursively so the plugin
# subdir (graphviz/graphviz/) and its config are preserved.
gv_local = os.path.join(PKG_DIR, "graphviz")
if os.path.isdir(gv_local):
    for root, _dirs, files in os.walk(gv_local):
        rel = os.path.relpath(root, gv_local)
        dest = "graphviz" if rel == "." else os.path.join("graphviz", rel)
        for name in files:
            binaries += [(os.path.join(root, name), dest)]

block_cipher = None

a = Analysis(
    [os.path.join(PKG_DIR, "desktop_app.py")],
    pathex=[SRC_ROOT, os.path.join(SRC_ROOT, "ddd_studio")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "pytest", "playwright", "pytest_bdd"],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DDD Studio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # windowed app, no console
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="DDD Studio",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="DDD Studio.app",
        icon=None,
        bundle_identifier="com.sofka.ddd-studio",
        info_plist={
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "11.0",
            "CFBundleShortVersionString": "1.0.0",
            "NSAppTransportSecurity": {"NSAllowsLocalNetworking": True},
        },
    )

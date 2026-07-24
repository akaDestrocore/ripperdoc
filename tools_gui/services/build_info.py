#!/usr/bin/env python

"""
File: build_info.py

Brief:
    Extract build information from git

Author:
    destrocore

Created: 2026-07-20
"""

from __future__ import annotations

import subprocess
import tools_gui.version as _version
from dataclasses import dataclass
from functools import lru_cache

UNKNOWN = "0.0.0"


@dataclass(frozen=True)
class BuildInfo:
    git_sha:str


def git_sha() -> str | None:
    try:
        result = subprocess.run(["git", "rev-parse", "--short=8", 
                                 "HEAD"], capture_output=True, text=True, 
                                 timeout=2, check=False)
    except (OSError, subprocess.SubprocessError):
        return None

    if 0 != result.returncode:
        return None

    return result.stdout.strip() or None


@lru_cache(maxsize=1)
def get_build_info() -> BuildInfo:
    try:
        from _version import GIT_SHA
    except ImportError:
        GIT_SHA = None

    if GIT_SHA is not None:
        return BuildInfo(git_sha=GIT_SHA)

    return BuildInfo(git_sha=git_sha() or UNKNOWN)
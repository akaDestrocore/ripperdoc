#!/usr/bin/env python

"""
File: merge.py

Brief:
    Merge bootloader and two images into a single output file.
Author:
    destrocore

Created: 2026-07-20
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from tools_gui.core.patch_header import PatchHeaderError, patch_bytes

PAD_BYTE = b"\xFF"

class MergeError(Exception):
    pass


@dataclass(frozen=True)
class MergeResult:
    output_bytes: bytes
    bootloader_size: int
    updater_size: int
    app_size: int
    total_size: int


@dataclass
class BinaryImage:
    offset: int
    base_addr: int
    version: tuple[int, int, int]
    security_version: int
    raw: bytes


def merge_bytes(bootloader: bytes, updater: BinaryImage, app: BinaryImage) -> MergeResult:

    if len(bootloader) > updater.offset:
        raise MergeError(f"Bootloader image will not fit in region FLASH. Region FLASH overflowed by {len(bootloader)-updater.offset} bytes")

    if len(updater.raw) > app.offset:
         raise MergeError(f"Updater image will not fit in region FLASH. Region FLASH overflowed by {len(updater.raw) - app.offset} bytes")

    pad1 = PAD_BYTE * (updater.offset - len(bootloader))
    pad2 = PAD_BYTE * (app.offset - len(updater.raw))

    merged = bootloader + pad1 + updater.raw + pad2 + app.raw

    return MergeResult(output_bytes=merged, 
                       bootloader_size=len(bootloader),
                       updater_size=len(updater.raw),
                       app_size=len(app.raw),
                       total_size=len(merged))


def patch_and_merge_bytes(bootloader: bytes, updater: BinaryImage, app: BinaryImage) -> MergeResult:
    try:
        updater_patched = patch_bytes(raw=updater.raw, base_addr=updater.base_addr, 
                                      version_major=updater.version[0], 
                                      version_minor=updater.version[1], 
                                      version_patch=updater.version[2], 
                                      security_version=updater.security_version)

    except PatchHeaderError as e:
        raise MergeError(f"Error patching updater:{e}") from e

    if "UPDATER" != updater_patched.image_type:
            raise MergeError(f"Selected updater slot contains an '{updater_patched.image_type}' image, expected UPDATER")

    try:
         app_patched = patch_bytes(raw=app.raw, base_addr=app.base_addr, 
                                   version_major=app.version[0],
                                   version_minor=app.version[1],
                                   version_patch=app.version[2],
                                   security_version=app.security_version)

    except PatchHeaderError as e:
        raise MergeError(f"Error patching app:{e}") from e

    if "APP" != app_patched.image_type:
         raise MergeError(f"Selected app slot contains an '{app_patched.image_type}' image, expected APP")

    return merge_bytes(bootloader=bootloader, updater=updater, app=app)
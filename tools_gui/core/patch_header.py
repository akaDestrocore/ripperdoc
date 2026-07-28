#!/usr/bin/python3

"""
File: patch_header.py

Brief:
    Patch the header of a binary file to update its fields with post build metadata.

Author:
    destrocore

Created: 2026-07-20
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

IMAGE_HDR_SIZE          = 0x200

IMAGE_MAGIC_APP         = 0xDEADC0DE
IMAGE_MAGIC_UPDATER     = 0xC0FFEE00
IMAGE_TYPE_APP          = 2
IMAGE_TYPE_UPDATER      = 1
IMAGE_HDR_VERSION       = 0x0100

OFFSET_IMAGE_MAGIC      = 0x00
OFFSET_IMAGE_HDR_VER    = 0x04
OFFSET_IMAGE_TYPE       = 0x06
OFFSET_FLAGS            = 0x07
OFFSET_VERSION_MAJOR    = 0x08
OFFSET_VERSION_MINOR    = 0x09
OFFSET_VERSION_PATCH    = 0x0A
OFFSET_KEY_ID           = 0x0B
OFFSET_SECURITY_VERSION = 0x0C
OFFSET_VECTOR           = 0x10
OFFSET_DATA_SIZE        = 0x14


MAGIC_TO_TYPE = {
    IMAGE_MAGIC_UPDATER: IMAGE_TYPE_UPDATER,
    IMAGE_MAGIC_APP: IMAGE_TYPE_APP,
}


NAME_TO_TYPE = {
    "UPDATER": IMAGE_TYPE_UPDATER,
    "APP": IMAGE_TYPE_APP,
}


MAGIC_NAMES = {
    IMAGE_MAGIC_UPDATER: "UPDATER",
    IMAGE_MAGIC_APP: "APP",
}


class PatchHeaderError(Exception):
    pass


@dataclass(frozen=True)
class PatchHeaderResult:
    output_bytes: bytes
    image_type: str
    data_size: int
    vector_addr:int
    version_major:int
    version_minor:int
    version_patch: int
    security_version: int


def read_image_type(raw: bytes) -> str:
    if len(raw) < IMAGE_HDR_SIZE:
        raise PatchHeaderError("Invalid image header size")
    
    image_type = struct.unpack_from("<B", raw, OFFSET_IMAGE_TYPE)[0]
    image_magic = struct.unpack_from("<I", raw, OFFSET_IMAGE_MAGIC)[0]
    image_hdr_ver = struct.unpack_from("<H", raw, OFFSET_IMAGE_HDR_VER)[0]

    if image_magic not in MAGIC_NAMES:
        raise PatchHeaderError(f"Bad magic: 0x{image_magic:08X}")

    if image_hdr_ver != IMAGE_HDR_VERSION:
        raise PatchHeaderError(f"Invalid image header version:{image_hdr_ver}")

    if image_type != MAGIC_TO_TYPE[image_magic]:
        raise PatchHeaderError(
            f"image_type byte 0x{image_type:02X} does not match magic "
            f"(expected 0x{MAGIC_TO_TYPE[image_magic]:02X} for {MAGIC_NAMES[image_magic]})"
        )

    return MAGIC_NAMES[image_magic]


def patch_bytes(raw: bytes, base_addr: int, version_major: int = 0, version_minor: int = 0, 
                version_patch: int = 0, security_version: int = 0, key_id: int = 0) -> PatchHeaderResult:

    image_type = read_image_type(raw)

    for name, value in (("version_major", version_major), ("version_minor", version_minor), 
                        ("version_patch", version_patch), ("key_id", key_id)):
        if not 0 <=value <= 0xFF:
            raise PatchHeaderError(f"{name}={value} is out of uint8_t range")

    header = bytearray(raw[:IMAGE_HDR_SIZE])
    data = raw[IMAGE_HDR_SIZE:]
    size = len(data)
    vector_addr = base_addr + IMAGE_HDR_SIZE
    struct.pack_into("<B", header, OFFSET_IMAGE_TYPE, NAME_TO_TYPE[image_type])
    struct.pack_into("<I", header, OFFSET_IMAGE_MAGIC, 
                     next(k for k, v in MAGIC_NAMES.items() if v == image_type))
    struct.pack_into("<B", header, OFFSET_VERSION_MAJOR, version_major)
    struct.pack_into("<B", header, OFFSET_VERSION_MINOR, version_minor)
    struct.pack_into("<B", header, OFFSET_VERSION_PATCH, version_patch)
    struct.pack_into("<B", header, OFFSET_KEY_ID, key_id)
    struct.pack_into("<I", header, OFFSET_SECURITY_VERSION, security_version)
    struct.pack_into("<I", header, OFFSET_VECTOR, vector_addr)
    struct.pack_into("<I", header, OFFSET_DATA_SIZE, size)
    output_bytes = bytes(header) + data

    return PatchHeaderResult(output_bytes=output_bytes, image_type=image_type, 
                             data_size=size, vector_addr=vector_addr, 
                             version_major=version_major, version_minor=version_minor,
                             version_patch=version_patch, security_version=security_version)
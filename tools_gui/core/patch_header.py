#!/usr/bin/env python

from __future__ import annotations

import struct
from dataclasses import dataclass

IMAGE_HDR_SIZE          = 0x200

IMAGE_MAGIC_APP         = 0xDEADC0DE
IMAGE_MAGIC_UPDATER     = 0xC0FFEE00

IMAGE_HDR_VERSION       = 0x0100

IMAGE_TYPE_UPDATER      = 1
IMAGE_TYPE_APP          = 2

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
    IMAGE_MAGIC_APP: IMAGE_TYPE_APP,
    IMAGE_MAGIC_UPDATER: IMAGE_TYPE_UPDATER,
}

MAGIC_NAMES = {
    IMAGE_MAGIC_APP: "APP",
    IMAGE_MAGIC_UPDATER: "UPDATER",
}

class PatchHeaderError(Exception):
    pass

@dataclass(frozen=True)
class PatchHeaderResult:
    output_bytes: bytes
    image_type: str
    data_size: int
    vector_addr: int
    version_major: int
    version_minor: int
    version_patch: int
    security_version: int


def read_header_type(raw: bytes) -> str:
    if len(raw) < IMAGE_HDR_SIZE:
        raise PatchHeaderError("Invalid binary size: binary smaller than header")
    # <IH => little-endian uint32_t + uint16_t
    magic, hdr_version = struct.unpack_from("<IH", raw, 0)

    if magic not in MAGIC_NAMES:
        raise PatchHeaderError(f"Bad magic: 0x{magic:08X}")

    if hdr_version != IMAGE_HDR_VERSION:
        raise PatchHeaderError(f"Bad header version: 0x{hdr_version:04X}")

    (image_type_byte,) = struct.unpack_from("<B", raw, OFFSET_IMAGE_TYPE)
    expected_type_byte = MAGIC_TO_TYPE[magic]
    if image_type_byte != expected_type_byte:
        raise PatchHeaderError(
            f"image_type byte 0x{image_type_byte:02X} does not match magic "
            f"(expected 0x{expected_type_byte:02X} for {MAGIC_NAMES[magic]})"
        )

    return MAGIC_NAMES[magic]


def patch_bytes( raw: bytes, base_addr: int, version_major: int = 0, version_minor: int = 0, 
                version_patch: int = 0, security_version: int = 0, key_id: int = 0, ) -> PatchHeaderResult:

    image_type = read_header_type(raw)
    
    for name, value in (
        ("version_major", version_major),
        ("version_minor", version_minor),
        ("version_patch", version_patch),
        ("key_id", key_id),
    ):
        if not 0 <= value <= 0xFF:
            raise PatchHeaderError(f"{name}={value} out of uint8_t range")

    header = bytearray(raw[:IMAGE_HDR_SIZE])
    data = raw[IMAGE_HDR_SIZE:]

    size = len(data)
    vector_addr = base_addr + IMAGE_HDR_SIZE

    struct.pack_into("<B", header, OFFSET_VERSION_MAJOR, version_major)
    struct.pack_into("<B", header, OFFSET_VERSION_MINOR, version_minor)
    struct.pack_into("<B", header, OFFSET_VERSION_PATCH, version_patch)
    struct.pack_into("<B", header, OFFSET_KEY_ID, key_id)
    struct.pack_into("<I", header, OFFSET_SECURITY_VERSION, security_version)
    struct.pack_into("<I", header, OFFSET_VECTOR, vector_addr)
    struct.pack_into("<I", header, OFFSET_DATA_SIZE, size)

    output_bytes = bytes(header) + data

    return PatchHeaderResult(
        output_bytes=output_bytes,
        image_type=image_type,
        data_size=size,
        vector_addr=vector_addr,
        version_major=version_major,
        version_minor=version_minor,
        version_patch=version_patch,
        security_version=security_version,
    )

def patch_file(input_path: str, output_path: str, base_addr: int, version_major: int = 0, 
            version_minor: int = 0, version_patch: int = 0, security_version: int = 0, key_id: int = 0, ) -> PatchHeaderResult:

    with open(input_path, "rb") as f:
            raw = f.read()
    
    result = patch_bytes(
        raw, base_addr, version_major, version_minor, version_patch, security_version, key_id
    )

    with open(output_path, "wb") as f:
        f.write(result.output_bytes)

    return result

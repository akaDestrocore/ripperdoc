#!/usr/bin/env python

"""
File: key_format_service.py

Brief:
    A service to encode and decode keys in various formats.

Author:
    destrocore

Created: 2026-07-20
"""

from __future__ import annotations

import re

FORMAT_HEX = "Hexadecimal"

SUPPORTED_FORMATS = (FORMAT_HEX,)


class KeyFormatError(ValueError):
    pass


def encode(raw: bytes, fmt: str) -> str:
    if fmt == FORMAT_HEX:
        return raw.hex()

    raise KeyFormatError(f"Unsupported format '{fmt}', expected one of {SUPPORTED_FORMATS}")


def encode_bytes_for_export(raw: bytes, fmt: str) -> bytes:
    if fmt == FORMAT_HEX:
        return raw

    raise KeyFormatError(f"Unsupported format '{fmt}', expected one of {SUPPORTED_FORMATS}")


def decode(text: str, fmt: str) -> bytes:
    text = text.strip()

    if not text:
        raise KeyFormatError("Empty input")

    if fmt == FORMAT_HEX:
        cleaned = re.sub(r"[\s:]", "", text)
        try:
            return bytes.fromhex(cleaned)
        except ValueError as exc:
            raise KeyFormatError(str(exc)) from exc

    raise KeyFormatError(f"Unsupported format '{fmt}', expected one of {SUPPORTED_FORMATS}")
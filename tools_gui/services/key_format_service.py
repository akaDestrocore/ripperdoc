from __future__ import annotations

from __future__ import annotations

import base64
import re

FORMAT_HEX = "Hexadecimal"
FORMAT_PEM = "PEM"

SUPPORTED_FORMATS = (FORMAT_HEX, FORMAT_PEM)
PEM_LINE_WIDTH = 64


def encode(raw: bytes, fmt: str) -> str:
    if fmt == FORMAT_HEX:
        return raw.hex()

    if fmt == FORMAT_PEM:
        length = len(raw)

        if length < 0x80:
            lengthBytes = bytes([length])
        else:
            lenBody = length.to_bytes((length.bit_length() + 7) // 8, "big")
            lengthBytes = bytes([0x80 | len(lenBody)]) + lenBody

        der = b"\x04" + lengthBytes + raw

        b64 = base64.b64encode(der).decode("ascii")

        body = "\n".join(
            b64[i:i + PEM_LINE_WIDTH]
            for i in range(0, len(b64), PEM_LINE_WIDTH)
        )

        return (
            f"-----BEGIN SYMMETRIC KEY-----\n"
            f"{body}\n"
            f"-----END SYMMETRIC KEY-----\n"
        )

    raise ValueError(f"Unsupported format '{fmt}', expected one of {SUPPORTED_FORMATS}")


def encode_bytes_for_export(raw: bytes, fmt: str) -> bytes:
    if fmt == FORMAT_HEX:
        return raw.hex().encode("ascii")

    if fmt == FORMAT_PEM:
        return encode(raw, FORMAT_PEM).encode("ascii")

    raise ValueError(f"Unsupported format '{fmt}', expected one of {SUPPORTED_FORMATS}")


def decode(text: str, fmt: str) -> bytes:
    text = text.strip()

    if not text:
        raise ValueError("Empty input")

    if fmt == FORMAT_HEX:
        cleaned = re.sub(r"[\s:]", "", text)
        return bytes.fromhex(cleaned)

    if fmt == FORMAT_PEM:
        match = re.search(
            r"-----BEGIN [^-]+-----\s*(.*?)\s*-----END [^-]+-----",
            text,
            re.DOTALL,
        )

        if match is None:
            raise ValueError("No PEM block found")

        der = base64.b64decode(
            "".join(match.group(1).split()),
            validate=True,
        )

        if len(der) < 2 or der[0] != 0x04:
            raise ValueError("Invalid DER OCTET STRING")

        firstLengthByte = der[1]

        if firstLengthByte < 0x80:
            length = firstLengthByte
            valueOffset = 2
        else:
            numLengthBytes = firstLengthByte & 0x7F

            if len(der) < (2 + numLengthBytes):
                raise ValueError("Truncated DER length")

            length = int.from_bytes(
                der[2:2 + numLengthBytes],
                "big",
            )

            valueOffset = 2 + numLengthBytes

        value = der[valueOffset:valueOffset + length]

        if len(value) != length:
            raise ValueError("Truncated DER value")

        return value

    raise ValueError(f"Unsupported format '{fmt}', expected one of {SUPPORTED_FORMATS}")
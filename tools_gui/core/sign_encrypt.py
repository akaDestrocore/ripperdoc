#!/usr/bin/env python

"""
File: sign_encrypt.py

Brief:
    Sign and encrypt a binary file using AES and ECC.

Author:
    destrocore

Created: 2026-07-20
"""

from __future__ import annotations

import os
import struct
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.PublicKey import ECC
from Crypto.Signature import DSS
from dataclasses import dataclass
from tools_gui.core.patch_header import PatchHeaderError, read_image_type

IMAGE_HDR_SIZE          = 0x200

OFFSET_FLAGS            = 0x07
OFFSET_NONCE            = 0x18
OFFSET_GCM_TAG          = 0x24
OFFSET_SHA256           = 0x36
OFFSET_SIGNATURE        = 0x54

NONCE_LEN               = 12
GCM_TAG_LEN             = 16
SHA256_LEN              = 32
SIGNATURE_LEN           = 64

IMAGE_FLAG_ENCRYPTED    = 1 << 0
IMAGE_FLAG_SIGNED       = 1 << 0


class SignEncryptError(Exception):
    pass


@dataclass(frozen=True)
class SignEncryptResult:
    output_bytes: bytes
    image_type: str
    data_size: int
    nonce: bytes
    tag: bytes
    sha256: bytes
    signature: bytes


def load_private_key(pem_text: str) -> ECC.EccKey:
    try:
        key = ECC.import_key(pem_text)
    except (ValueError, TypeError, IndexError) as e:
        raise SignEncryptError(f"Failed to load private key: {e}") from e

    if key.curve not in ('NIST P-256', 'p256', 'P-256', 'prime256v1', 'secp256r1'):
        raise SignEncryptError(f"Expected P-256 key, got curve={key.curve}")

    return key


def load_aes_key(raw: bytes) -> bytes:
    if len(raw) != 32:
        raise RuntimeError(f"AES key must be 32 bytes, got {len(raw)}")
    return raw


def validate_signable_header(raw: bytes) -> str:
    try:
        image_type = read_image_type(raw)
    except PatchHeaderError as e:
        raise SignEncryptError(f"{e}") from e

    if image_type not in ('UPDATER', 'APP'):
        raise PatchHeaderError(f"Image is not signable, type={image_type}")

    return image_type


def aes_gcm_encrypt(data: bytes, key: bytes, nonce: bytes) -> bytes:
    if 12 != len(nonce):
        raise RuntimeError(f"GCM is most commonly used with 96-bit (12-byte) nonces, which is the length recommended by NIST SP 800-38D."
                           f"Received nonce lenght is {len(nonce)}")

    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(data)

    return ciphertext, tag


def sign_data(priv_key: ECC.EccKey, data: bytes) -> tuple[bytes, bytes]:
    h = SHA256.new()
    digest = h.digest()

    signer = DSS.new(key=priv_key, mode="fips-186-3", encoding="binary")
    signature = signer.sign(h)

    return digest, signature


def process_bytes(raw: bytes, priv_key: ECC.EccKey, aes_key: bytes, nonce: bytes | None = None, 
                  require_valid_header: bool = True) -> SignEncryptResult:

    if len(raw) < IMAGE_HDR_SIZE:
        raise SignEncryptError(f"Received data length is {len(raw)}."
                               f"Header size must be {IMAGE_HDR_SIZE} bytes")

    image_type = validate_signable_header(raw)

    if require_valid_header != True:
        image_type = "UNKNOWN"

    if nonce is None:
        nonce = os.urandom(NONCE_LEN)

    header = bytearray(raw[:IMAGE_HDR_SIZE])
    plaintext_data = raw[IMAGE_HDR_SIZE:]

    digest, signature = sign_data(priv_key, plaintext_data)
    ciphertext, tag = aes_gcm_encrypt(plaintext_data, aes_key, nonce)

    struct.pack_into(f"<{NONCE_LEN}s", header, OFFSET_NONCE, nonce)
    struct.pack_into(f"<{GCM_TAG_LEN}s", header, OFFSET_GCM_TAG, tag)
    struct.pack_into(f"<{SHA256_LEN}s", header, OFFSET_SHA256, digest)
    struct.pack_into(f"{SIGNATURE_LEN}s", header, OFFSET_SIGNATURE, signature)
    header[OFFSET_FLAGS] |= (IMAGE_FLAG_ENCRYPTED | IMAGE_FLAG_SIGNED)

    output_bytes = bytes(header) + ciphertext

    return SignEncryptResult(output_bytes=output_bytes, 
                             image_type=image_type,
                             data_size=len(plaintext_data), 
                             nonce=nonce, tag=tag, 
                             sha256=digest, signature=signature)

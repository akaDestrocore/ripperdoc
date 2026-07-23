from __future__ import annotations

import os
import struct
from dataclasses import dataclass
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.PublicKey import ECC
from Crypto.Signature import DSS

from tools_gui.core.patch_header import PatchHeaderError, read_header_type

IMAGE_HDR_SIZE          = 0x200

OFFSET_FLAGS            = 0x07
OFFSET_NONCE            = 0x18
OFFSET_GCM_TAG          = 0x24
OFFSET_SHA256           = 0x34
OFFSET_SIGNATURE        = 0x54

NONCE_LEN               = 12
SHA256_LEN              = 32
SIGNATURE_LEN           = 64
TAG_LEN                 = 16

IMAGE_FLAG_ENCRYPTED    = 1 << 0
IMAGE_FLAG_SIGNED       = 1 << 1

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
    except (ValueError, IndexError, TypeError) as exc:
        raise SignEncryptError(f"Could not parse private key: {exc}") from exc

    if key.curve not in ("p256", "P-256", "NIST P-256", "secp256r1"):
        raise SignEncryptError(f"Expected P-256 key, got curve={key.curve}")

    return key


def load_aes_key(raw: bytes) -> bytes:
    if len(raw) != 32:
        raise RuntimeError(f"AES key must be 32 bytes, got {len(raw)}")
    return raw


def validate_signable_header(raw: bytes) -> str:
    try:
        image_type = read_header_type(raw)
    except PatchHeaderError as exc:
        raise SignEncryptError(str(exc)) from exc

    if image_type not in ("APP", "UPDATER"):
        raise SignEncryptError(f"Image type '{image_type}' is not signable")

    return image_type


def aes_gcm_encrypt(key: bytes, nonce: bytes, plaintext: bytes) -> tuple[bytes, bytes]:
    if NONCE_LEN != len(nonce):
        raise SignEncryptError(f"nonce must be {NONCE_LEN} bytes")

    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)

    if len(tag) != TAG_LEN:
        raise SignEncryptError(f"Unexpected GCM tag length {len(tag)}")

    return ciphertext, tag

def sign_data(priv_key: ECC.EccKey, data: bytes) -> tuple[bytes, bytes]:
    h = SHA256.new(data)
    digest = h.digest()

    signer = DSS.new(priv_key, "fips-186-3", encoding="binary")
    signature = signer.sign(h)

    if len(signature) != SIGNATURE_LEN:
        raise SignEncryptError(f"unexpected signature length {len(signature)}")

    return digest, signature


def process_bytes(raw: bytes, priv_key: ECC.EccKey, aes_key: bytes,
                nonce: bytes | None = None,
                require_valid_header: bool = True,
                ) -> SignEncryptResult:

    if len(raw) < IMAGE_HDR_SIZE:
        raise SignEncryptError("Input smaller than IMAGE_HDR_SIZE")

    image_type = validate_signable_header(raw) if require_valid_header else "UNKNOWN"

    if nonce is None:
        nonce = os.urandom(NONCE_LEN)

    header = bytearray(raw[:IMAGE_HDR_SIZE])
    plaintext_data = raw[IMAGE_HDR_SIZE:]

    digest, signature = sign_data(priv_key, plaintext_data)
    ciphertext, tag = aes_gcm_encrypt(aes_key, nonce, plaintext_data)

    struct.pack_into(f"<{NONCE_LEN}s", header, OFFSET_NONCE, nonce)
    struct.pack_into(f"<{SHA256_LEN}s", header, OFFSET_SHA256, digest)
    struct.pack_into(f"<{SIGNATURE_LEN}s", header, OFFSET_SIGNATURE, signature)
    struct.pack_into(f"<{TAG_LEN}s", header, OFFSET_GCM_TAG, tag)
    header[OFFSET_FLAGS] |= (IMAGE_FLAG_ENCRYPTED | IMAGE_FLAG_SIGNED)

    output_bytes = bytes(header) + ciphertext

    return SignEncryptResult(
        output_bytes=output_bytes,
        image_type=image_type,
        data_size=len(plaintext_data),
        nonce=nonce, tag=tag, sha256=digest, 
        signature=signature,
    )


def process_file(input_path: str, output_path: str,
                priv_key_path: str, aes_key_path: str,
                nonce: bytes | None = None,
                ) -> SignEncryptResult:

    with open(input_path, "rb") as f:
        raw = f.read()

    with open(priv_key_path, "rt") as f:
        priv_key = load_private_key(f.read())

    with open(aes_key_path, "rb") as f:
        aes_key = load_aes_key(f.read())

    result = process_bytes(raw, priv_key, aes_key, nonce)

    with open(output_path, "wb") as f:
        f.write(result.output_bytes)

    return result
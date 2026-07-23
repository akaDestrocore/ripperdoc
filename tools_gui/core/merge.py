from __future__ import annotations

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


def merge_bytes(bootloader: bytes, updater: bytes,
                app: bytes, updater_offset: int,
                app_offset: int) -> MergeResult:
    
    if len(bootloader) > updater_offset:
        raise MergeError("Bootloader too large")

    if len(updater) > (app_offset - updater_offset):
        raise MergeError("Updater too large")

    pad1 = PAD_BYTE * (updater_offset - len(bootloader))
    pad2 = PAD_BYTE * (app_offset - updater_offset - len(updater))

    merged = bootloader + pad1 + updater + pad2 + app

    return MergeResult(
        output_bytes=merged,
        bootloader_size=len(bootloader),
        updater_size=len(updater),
        app_size=len(app),
        total_size=len(merged),
    )


def merge_files(boot_path: str, updater_path: str,
                app_path: str, output_path: str,
                updater_offset: int, app_offset: int) -> MergeResult:
    with open(boot_path, "rb") as f:
        bootloader = f.read()

    with open(updater_path, "rb") as f:
        updater = f.read()

    with open(app_path, "rb") as f:
        app = f.read()

    result = merge_bytes(bootloader, updater, app, updater_offset, app_offset)

    with open(output_path, "wb") as f:
        f.write(result.output_bytes)

    return result


def patch_and_merge_bytes(bootloader: bytes, updater_raw: bytes,
                        app_raw: bytes, updater_offset: int,
                        app_offset: int, updater_base_addr: int,
                        app_base_addr: int, updater_version: tuple[int, int, int] = (0, 0, 0),
                        updater_security_version: int = 0, app_version: tuple[int, int, int] = (0, 0, 0),
                        app_security_version: int = 0 ) -> MergeResult:

    try:
        updater_patched = patch_bytes(
            updater_raw,
            updater_base_addr,
            version_major=updater_version[0],
            version_minor=updater_version[1],
            version_patch=updater_version[2],
            security_version=updater_security_version,
        )
    except PatchHeaderError as exc:
        raise MergeError(f"Updater header invalid: {exc}") from exc

    if updater_patched.image_type != "UPDATER":
        raise MergeError(
            f"Selected updater slot contains an '{updater_patched.image_type}' image, expected UPDATER"
        )

    try:
        app_patched = patch_bytes(
            app_raw,
            app_base_addr,
            version_major=app_version[0],
            version_minor=app_version[1],
            version_patch=app_version[2],
            security_version=app_security_version,
        )
    except PatchHeaderError as exc:
        raise MergeError(f"Application header invalid: {exc}") from exc

    if app_patched.image_type != "APP":
        raise MergeError(
            f"Selected application slot contains a '{app_patched.image_type}' image, expected APP"
        )

    return merge_bytes(
        bootloader,
        updater_patched.output_bytes,
        app_patched.output_bytes,
        updater_offset,
        app_offset,
    )
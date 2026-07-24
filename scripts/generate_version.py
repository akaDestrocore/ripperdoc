from __future__ import annotations

import subprocess
from pathlib import Path

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "tools_gui" / "version.py"


def main() -> None:
    sha = subprocess.check_output(["git", "rev-parse", "--short=8", "HEAD"], text=True).strip()

    OUTPUT_PATH.write_text("# Auto-generated at build time - DO NOT edit\n" f'GIT_SHA = "{sha}"\n', encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} with GIT_SHA={sha}")

if __name__ == "__main__":
    main()
from __future__ import annotations

import json
from pathlib import Path

DEFAULT_LANGUAGE = "en"
FALLBACK_LANGUAGE = "en"
SUPPORTED_LANGUAGES = ("en", "tr")

_I18N_DIR = Path(__file__).resolve().parent.parent / "i18n"


class I18nService:

    def __init__(self, language: str = DEFAULT_LANGUAGE, i18n_dir: Path | None = None) -> None:
        self._i18n_dir = i18n_dir or _I18N_DIR
        self._catalogs: dict[str, dict[str, str]] = {}
        self._language = DEFAULT_LANGUAGE
        self.set_language(language)

    @property
    def language(self) -> str:
        return self._language

    def set_language(self, language: str) -> None:
        if language not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language '{language}', expected one of {SUPPORTED_LANGUAGES}")

        self._ensure_loaded(language)
        self._ensure_loaded(FALLBACK_LANGUAGE)
        self._language = language

    def t(self, key: str) -> str:
        catalog = self._catalogs.get(self._language, {})
        if key in catalog:
            return catalog[key]

        fallback = self._catalogs.get(FALLBACK_LANGUAGE, {})
        if key in fallback:
            return fallback[key]

        return f"!!{key}!!"

    def _ensure_loaded(self, language: str) -> None:
        if language in self._catalogs:
            return

        catalog_path = self._i18n_dir / f"{language}.json"
        with open(catalog_path, "r", encoding="utf-8") as f:
            self._catalogs[language] = json.load(f)
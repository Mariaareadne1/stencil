"""Contract test: packages/types/index.ts must mirror the Pydantic schemas.

The web app consumes the API through these hand-written TypeScript types, so
a field added or renamed on one side only is a silent runtime bug. This test
compares field names for every model that exists on both sides.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import BaseModel

from apps.api.models import schemas

TYPES_FILE = Path(__file__).resolve().parents[3] / "packages" / "types" / "index.ts"

_INTERFACE_RE = re.compile(r"export interface (\w+)\s*\{(.*?)\n\}", re.S)
_FIELD_RE = re.compile(r"^\s*(\w+)\??\s*:", re.M)


def _ts_interfaces() -> dict[str, set[str]]:
    source = TYPES_FILE.read_text(encoding="utf-8")
    return {
        name: set(_FIELD_RE.findall(body))
        for name, body in _INTERFACE_RE.findall(source)
    }


def _pydantic_models() -> dict[str, type[BaseModel]]:
    return {
        name: obj
        for name, obj in vars(schemas).items()
        if isinstance(obj, type) and issubclass(obj, BaseModel) and obj is not BaseModel
    }


TS = _ts_interfaces()
PY = _pydantic_models()
SHARED = sorted(set(TS) & set(PY))


def test_core_models_are_shared() -> None:
    for name in ("CreateJobRequest", "Persona", "BrandAssets", "BrandResult", "Job"):
        assert name in SHARED, f"{name} missing from Pydantic or TypeScript side"


@pytest.mark.parametrize("name", SHARED)
def test_field_names_match(name: str) -> None:
    py_fields = set(PY[name].model_fields)
    ts_fields = TS[name]
    assert py_fields == ts_fields, (
        f"{name}: only in Python {sorted(py_fields - ts_fields)}, "
        f"only in TypeScript {sorted(ts_fields - py_fields)}"
    )

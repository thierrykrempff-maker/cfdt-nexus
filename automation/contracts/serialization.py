"""Stable JSON-compatible serialization helpers for common contracts."""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


def require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def freeze_json(value: Any, path: str = "metadata") -> Any:
    """Copy and recursively freeze a JSON-compatible value."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        frozen: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{path} keys must be strings")
            frozen[key] = freeze_json(item, f"{path}.{key}")
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(freeze_json(item, f"{path}[]") for item in value)
    raise TypeError(f"{path} must contain only JSON-compatible values")


def freeze_metadata(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    frozen = freeze_json(value or {}, "metadata")
    json.dumps(to_json_value(frozen), ensure_ascii=False, sort_keys=True)
    return frozen


def to_json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): to_json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, frozenset)):
        return [to_json_value(item) for item in value]
    if is_dataclass(value):
        return {field.name: to_json_value(getattr(value, field.name)) for field in fields(value)}
    raise TypeError(f"value of type {type(value).__name__} is not JSON-compatible")


def contract_to_dict(value: Any) -> dict[str, Any]:
    result = to_json_value(value)
    if not isinstance(result, dict):
        raise TypeError("contract serialization must produce a dictionary")
    return result


def parse_datetime(value: Any, field_name: str) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, str):
        try:
            result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"{field_name} must be an ISO-8601 datetime") from exc
    else:
        raise TypeError(f"{field_name} must be a datetime or ISO-8601 string")
    if result.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone")
    return result


def parse_date(value: Any, field_name: str) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be an ISO-8601 date") from exc
    raise TypeError(f"{field_name} must be a date or ISO-8601 string")


def reject_unknown_fields(value: Mapping[str, Any], allowed: set[str], contract_name: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ValueError(f"{contract_name} contains unknown field(s): {', '.join(unknown)}")

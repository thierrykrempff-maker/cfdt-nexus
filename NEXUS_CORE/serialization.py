"""Deterministic and privacy-aware serialization for Nexus Core models."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
import json
from typing import TypeAlias

from .privacy import DataSensitivity, MetadataEntry, RedactionStatus


JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


def _metadata_entry(entry: MetadataEntry, redact_sensitive: bool) -> dict[str, JsonValue]:
    sensitive = entry.sensitivity is not DataSensitivity.NON_SENSITIVE
    value: JsonValue = "<redacted>" if redact_sensitive and sensitive else to_primitive(
        entry.value, redact_sensitive=redact_sensitive
    )
    status = RedactionStatus.REDACTED if redact_sensitive and sensitive else entry.redaction_status
    return {
        "key": entry.key,
        "redaction_status": status.value,
        "sensitivity": entry.sensitivity.value,
        "value": value,
    }


def to_primitive(value: object, *, redact_sensitive: bool = True) -> JsonValue:
    """Convert supported models into stable JSON-compatible primitives."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return to_primitive(value.value, redact_sensitive=redact_sensitive)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, MetadataEntry):
        return _metadata_entry(value, redact_sensitive)
    if isinstance(value, tuple):
        return [to_primitive(item, redact_sensitive=redact_sensitive) for item in value]
    if isinstance(value, list):
        return [to_primitive(item, redact_sensitive=redact_sensitive) for item in value]
    if isinstance(value, dict):
        return {
            str(key): to_primitive(value[key], redact_sensitive=redact_sensitive)
            for key in sorted(value, key=str)
        }
    if is_dataclass(value) and not isinstance(value, type):
        result: dict[str, JsonValue] = {}
        for item in fields(value):
            field_value = getattr(value, item.name)
            if item.name == "value" and value.__class__.__module__.endswith(".values"):
                result[item.name] = "<redacted>" if redact_sensitive else to_primitive(
                    field_value, redact_sensitive=False
                )
            else:
                result[item.name] = to_primitive(
                    field_value, redact_sensitive=redact_sensitive
                )
        return result
    raise TypeError(f"unsupported serialization type: {type(value).__name__}")


def to_json(value: object, *, redact_sensitive: bool = True) -> str:
    """Serialize using stable key ordering and compact UTF-8 JSON syntax."""

    return json.dumps(
        to_primitive(value, redact_sensitive=redact_sensitive),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )

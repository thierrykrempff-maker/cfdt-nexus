"""Structural contracts for connector snapshots, adaptation and reporting."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import (
    ConnectorAdapterInput, ConnectorAdapterReport, ConnectorAdapterResult,
    ConnectorResponseSnapshot, ConnectorValidationReport,
)


@runtime_checkable
class ConnectorSnapshotProvider(Protocol):
    def snapshot(self) -> ConnectorResponseSnapshot: ...


@runtime_checkable
class ConnectorAdapter(Protocol):
    def adapt(self) -> ConnectorAdapterResult: ...


@runtime_checkable
class ConnectorAdapterReporter(Protocol):
    def render(self, report: ConnectorAdapterReport) -> str: ...


@runtime_checkable
class ConnectorAdapterValidatorProtocol(Protocol):
    def validate(self, source: ConnectorAdapterInput,
                 result: ConnectorAdapterResult) -> ConnectorValidationReport: ...

"""Public metadata-only facade for complementary official connectors."""

from .connector import ComplementaryOfficialConnector
from .platform import (
    COMPLEMENTARY_CONNECTOR_CONTRACTS,
    COMPLEMENTARY_CONNECTOR_REGISTRY,
    COMPLEMENTARY_CONNECTOR_SPECS,
)

__all__ = (
    "COMPLEMENTARY_CONNECTOR_CONTRACTS",
    "COMPLEMENTARY_CONNECTOR_REGISTRY",
    "COMPLEMENTARY_CONNECTOR_SPECS",
    "ComplementaryOfficialConnector",
)

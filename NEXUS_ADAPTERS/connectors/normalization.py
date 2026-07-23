"""Closed mapping tables from connector vocabulary to existing Core enums."""

from __future__ import annotations

from NEXUS_CORE import DocumentType, SourceType

from .models import ConnectorSourceCategory


class ConnectorSourceNormalizer:
    _SOURCES = {
        ConnectorSourceCategory.LEGISLATION: SourceType.LEGAL_DATABASE,
        ConnectorSourceCategory.REGULATION: SourceType.LEGAL_DATABASE,
        ConnectorSourceCategory.CASE_LAW: SourceType.LEGAL_DATABASE,
        ConnectorSourceCategory.ADMINISTRATIVE_DOCTRINE: SourceType.OFFICIAL_WEBSITE,
        ConnectorSourceCategory.INDEPENDENT_AUTHORITY: SourceType.OFFICIAL_WEBSITE,
        ConnectorSourceCategory.COLLECTIVE_AGREEMENT: SourceType.INTERNAL_REFERENTIAL,
        ConnectorSourceCategory.COMPANY_AGREEMENT: SourceType.INTERNAL_REFERENTIAL,
        ConnectorSourceCategory.SOCIAL_SECURITY_BODY: SourceType.OFFICIAL_WEBSITE,
        ConnectorSourceCategory.INTERNAL_DOCUMENT: SourceType.INTERNAL_REFERENTIAL,
        ConnectorSourceCategory.OTHER_OFFICIAL: SourceType.OFFICIAL_WEBSITE,
        ConnectorSourceCategory.UNKNOWN: SourceType.UNKNOWN,
    }
    _DOCUMENTS = {
        "LEGISLATION": DocumentType.LEGAL_TEXT,
        "REGULATION": DocumentType.LEGAL_TEXT,
        "LEGAL_TEXT": DocumentType.LEGAL_TEXT,
        "CASE_LAW": DocumentType.CASE_LAW,
        "JURISPRUDENCE": DocumentType.CASE_LAW,
        "COLLECTIVE_AGREEMENT": DocumentType.COLLECTIVE_AGREEMENT,
        "COMPANY_AGREEMENT": DocumentType.COLLECTIVE_AGREEMENT,
        "SOCIAL_PROTECTION_NOTICE": DocumentType.SOCIAL_PROTECTION_NOTICE,
    }

    def source_type(self, category: ConnectorSourceCategory) -> SourceType:
        return self._SOURCES[category]

    def document_type(self, value: str) -> DocumentType:
        return self._DOCUMENTS.get(value.upper(), DocumentType.OTHER)

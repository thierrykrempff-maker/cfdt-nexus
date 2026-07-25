"""Final publication challenger."""

from __future__ import annotations

from .models import CriticResult, NormalizedEngineResult

_SENSITIVE_ASSERTIONS = (
    "certain",
    "illégal",
    "entrave",
    "harcèlement établi",
    "discrimination établie",
)


class FinalCritic:
    def review(
        self,
        results: tuple[NormalizedEngineResult, ...],
        rendered_summary: str,
    ) -> CriticResult:
        fragile = []
        corrections = []
        lowered = rendered_summary.lower()
        for marker in _SENSITIVE_ASSERTIONS:
            if marker in lowered and not any(result.evidence for result in results):
                fragile.append(f"Formulation insuffisamment étayée : {marker}")
                corrections.append("Remplacer l'affirmation par une hypothèse à vérifier.")
        if not any(result.employer_arguments for result in results):
            fragile.append("Arguments employeur non documentés.")
        verdict = "BLOCKED" if corrections else "PUBLISH_WITH_WARNINGS" if fragile else "PUBLISHABLE"
        return CriticResult(
            ("Sources et limites conservées.", "Actions présentées comme brouillons."),
            tuple(fragile),
            tuple(corrections),
            verdict,
        )

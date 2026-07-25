"""Conservative conflict detection and resolution."""

from __future__ import annotations

from .models import Conflict, NormalizedEngineResult


_AFFIRMATIVE = ("certain", "établi", "illégal", "acquis")
_BLOCKING = ("bloquant", "calcul impossible", "donnée insuffisante")


class ContradictionResolver:
    def resolve(self, results: tuple[NormalizedEngineResult, ...]) -> tuple[Conflict, ...]:
        conflicts: list[Conflict] = []
        for index, left in enumerate(results):
            for right in results[index + 1 :]:
                left_text = " ".join((*left.possible_qualifications, *left.strategies)).lower()
                right_text = " ".join((*right.possible_qualifications, *right.strategies)).lower()
                if any(marker in left_text for marker in _AFFIRMATIVE) != any(
                    marker in right_text for marker in _AFFIRMATIVE
                ) and (left_text and right_text):
                    conflicts.append(
                        Conflict(
                            "prudence",
                            (left.engine, right.engine),
                            "Les moteurs n'emploient pas le même niveau d'affirmation.",
                            "La formulation la plus prudente est conservée.",
                            tuple(dict.fromkeys((*left.missing_information, *right.missing_information))),
                        )
                    )
                if any(marker in left_text for marker in _BLOCKING) or any(
                    marker in right_text for marker in _BLOCKING
                ):
                    conflicts.append(
                        Conflict(
                            "blocking_rule",
                            (left.engine, right.engine),
                            "Une règle bloquante interdit une conclusion ou un calcul.",
                            "Le calcul ou la conclusion est suspendu jusqu'à vérification.",
                            tuple(dict.fromkeys((*left.missing_information, *right.missing_information))),
                        )
                    )
        unique = {(item.conflict_type, item.engines): item for item in conflicts}
        return tuple(unique[key] for key in sorted(unique))

import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "automation" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import assistant_ds_router as router  # noqa: E402


def test_cse_convocation_on_rest_day_is_not_disciplinary() -> None:
    route = router.route_query(
        "Un élu en 5x8 convoqué à une réunion CSE pendant son jour de repos "
        "demande comment ce temps sera payé."
    )

    assert "disciplinaire" not in route["domains"]
    assert route["employee_path"] == "QUESTION_SALARIE"

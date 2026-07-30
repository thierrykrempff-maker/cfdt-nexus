from dataclasses import FrozenInstanceError

import pytest

from SYNDICAL_REASONING_ENGINE import MeetingBody, PVSearchMode
from tests.cse_cssct_test_support import pv_query


def test_contracts_are_immutable_and_serializable():
    query = pv_query("pause")
    assert query.to_dict()["body_scope"] == [MeetingBody.CSE.value, MeetingBody.CE.value]
    with pytest.raises(FrozenInstanceError):
        query.max_results = 10
    assert PVSearchMode.HYBRID_LOCAL.value == "HYBRID_LOCAL"

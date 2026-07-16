from enum import StrEnum

class ConnectorState(StrEnum):
    ARCHITECTURE_ONLY="architecture_only"
    ACCESS_REVIEW_COMPLETE="access_review_complete"
    CONNECTOR_DESIGN_COMPLETE="connector_design_complete"
    IMPLEMENTED="implemented"
    VALIDATED="validated"
    ENABLED="enabled"
    DISABLED="disabled"
    DEPRECATED="deprecated"
    BLOCKED="blocked"

TRANSITIONS={
 ConnectorState.ARCHITECTURE_ONLY:{ConnectorState.ACCESS_REVIEW_COMPLETE,ConnectorState.BLOCKED},
 ConnectorState.ACCESS_REVIEW_COMPLETE:{ConnectorState.CONNECTOR_DESIGN_COMPLETE,ConnectorState.BLOCKED},
 ConnectorState.CONNECTOR_DESIGN_COMPLETE:{ConnectorState.IMPLEMENTED,ConnectorState.BLOCKED},
 ConnectorState.IMPLEMENTED:{ConnectorState.VALIDATED,ConnectorState.BLOCKED},
 ConnectorState.VALIDATED:{ConnectorState.ENABLED,ConnectorState.DISABLED,ConnectorState.BLOCKED},
 ConnectorState.ENABLED:{ConnectorState.DISABLED,ConnectorState.DEPRECATED,ConnectorState.BLOCKED},
 ConnectorState.DISABLED:{ConnectorState.ENABLED,ConnectorState.DEPRECATED,ConnectorState.BLOCKED},
 ConnectorState.DEPRECATED:set(), ConnectorState.BLOCKED:{ConnectorState.DISABLED},
}

def can_transition(current:ConnectorState,target:ConnectorState)->bool:return target in TRANSITIONS[current]

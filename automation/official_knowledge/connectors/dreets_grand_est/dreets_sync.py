"""Synchronization is deliberately unavailable."""
from . import DREETS_GRAND_EST_NETWORK_NOT_IMPLEMENTED

def synchronize(*_args,**_kwargs):raise RuntimeError(DREETS_GRAND_EST_NETWORK_NOT_IMPLEMENTED)

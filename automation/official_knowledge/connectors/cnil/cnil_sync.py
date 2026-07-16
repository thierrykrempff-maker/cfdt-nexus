"""Synchronization contract only; execution is unavailable."""
from . import CNIL_NETWORK_NOT_IMPLEMENTED

def synchronize(*_args,**_kwargs):raise RuntimeError(CNIL_NETWORK_NOT_IMPLEMENTED)

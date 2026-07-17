"""Synchronization contract only; execution is unavailable."""
from .cnil_platform import network_not_implemented

def synchronize(*_args,**_kwargs):raise network_not_implemented()

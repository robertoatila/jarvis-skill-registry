"""
adapters // J.A.R.V.I.S. Agentic Integration Adapters
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
"""

from .local import LocalAction, LocalActionAdapter, LocalActionResult, LocalAdapterType, LocalActionError, ConcurrencyConflictError

__all__ = [
    "LocalAction",
    "LocalActionAdapter",
    "LocalActionResult",
    "LocalAdapterType",
    "LocalActionError",
    "ConcurrencyConflictError"
]

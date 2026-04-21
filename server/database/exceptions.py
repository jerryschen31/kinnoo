"""Database-specific exception types."""

from __future__ import annotations


class DatabaseError(RuntimeError):
    """Base class for registry database failures."""


class DatabaseUnavailableError(DatabaseError):
    """Raised when database connectivity checks fail."""


class DatabaseConflictError(DatabaseError):
    """Raised when writes violate unique constraints or expected invariants."""

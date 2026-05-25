"""Exceptions raised while reading plocate databases."""

class PlocateDatabaseError(Exception):
    """Base error for plocate database operations."""


class PlocateFormatError(PlocateDatabaseError):
    """The file is missing or not a valid plocate database."""

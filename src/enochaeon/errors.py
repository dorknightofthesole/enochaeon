"""Errors the CLI reports to a person."""


class EnochaeonError(Exception):
    """A problem the caller can fix: a missing tool, an unknown letter, a collision."""

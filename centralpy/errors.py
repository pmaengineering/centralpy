"""Module for custom exceptions in centralpy source code."""


class CentralpyError(Exception):
    """Base class for central exceptions."""


class AuthenticationError(CentralpyError):
    """An exception related to authentication."""


class AuditReportError(CentralpyError):
    """An exception for an AuditReport in an inconsistent state."""

"""Module for custom exceptions in centralpy source code."""


class CentralException(Exception):
    """Base class for central exceptions"""


class AuthenticationException(CentralException):
    """An exception related to authentication"""

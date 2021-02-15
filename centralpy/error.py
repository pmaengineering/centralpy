class CentralException(Exception):
    """Base class for central exceptions"""


class AuthenticationException(CentralException):
    """An exception related to authentication"""
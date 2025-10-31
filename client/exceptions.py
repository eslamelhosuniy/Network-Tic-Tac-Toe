# client/exceptions.py

from ssl import SSLCertVerificationError, SSLError


class NetworkError(Exception):
    pass

class ConnectionFailedError(NetworkError):
    pass

class ConnectionLostError(NetworkError):
    pass

class TimeoutNetworkError(NetworkError):
    pass

class SendDataError(NetworkError):
    pass

class ReceiveDataError(NetworkError):
    pass

class HandshakeError(SSLError):
    pass

class SSLCertificateError(SSLCertVerificationError ):
    pass
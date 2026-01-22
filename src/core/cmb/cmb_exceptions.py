class TransportError(Exception):
    def __init__(self, tx_id, reason, details=None):
        self.tx_id = tx_id
        self.reason = reason
        self.details = details
        super().__init__(reason)

class AckTimeoutError(TransportError):
    pass

class InvalidAckError(TransportError):
    pass

class ProtocolViolationError(TransportError):
    pass

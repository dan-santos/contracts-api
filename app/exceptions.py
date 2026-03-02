class ContractCancellationError(Exception):
    pass

class ContractCancellationConflictError(Exception):
    pass

class ContractCancellationUnexpectedError(Exception):
    pass

class ContractReprocessingError(Exception):
    pass

class ContractNotFoundError(Exception):
    pass
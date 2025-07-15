from enum import Enum
from typing import TypedDict

class OperationType(Enum):
    CALL = 0
    DELEGATE_CALL = 1

class SafeTransaction(TypedDict):
    to: str
    value: int
    data: bytes
    operation: OperationType

from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any


def serialize(value: Any) -> Any:
    """
    Convert Tradewisser's internal Python objects into
    JSON-safe Python values.

    The function recursively handles:
    - dataclasses
    - dictionaries
    - lists
    - tuples
    - enums
    - normal Python objects
    - primitive values
    """

    # 1. None, strings, numbers, booleans
    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    # 2. Enums
    if isinstance(value, Enum):
        return value.value

    # 3. Dataclasses
    if is_dataclass(value):
        return serialize(asdict(value))

    # 4. Dictionaries
    if isinstance(value, dict):
        return {
            str(key): serialize(item)
            for key, item in value.items()
        }

    # 5. Lists, tuples and sets
    if isinstance(value, (list, tuple, set)):
        return [
            serialize(item)
            for item in value
        ]

    # 6. Normal Python objects
    if hasattr(value, "__dict__"):
        return serialize(vars(value))

    # 7. Fallback
    return str(value)


def serialize_analysis_result(result: dict) -> dict:
    """
    Serialize the complete result returned by
    TradewisserAnalysisService.analyze().
    """

    return serialize(result)
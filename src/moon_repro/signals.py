from functools import reduce
from operator import or_
from pathlib import Path

SIGNAL_BITS = (2, 4, 8)
EVERY_SIGNAL = reduce(or_, SIGNAL_BITS)
TOLERATED_CODES = tuple(range(2, EVERY_SIGNAL + 1, 2))


def as_bits(code: int) -> str:
    return f"{code:04b}"


def finished_marker(name: str) -> Path:
    return Path(f".{name}-finished")


def signal_record(name: str) -> Path:
    return Path(f".{name}-signal")


def recorded_signals() -> list[Path]:
    return sorted(Path().glob(".*-signal"))

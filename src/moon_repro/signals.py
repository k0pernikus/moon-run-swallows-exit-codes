from functools import reduce
from operator import or_
from pathlib import Path

SIGNAL_EXIT_BASE = 64
SIGNAL_BITS = (2, 4, 8)
EVERY_SIGNAL = reduce(or_, SIGNAL_BITS)


def exit_code(signals: int) -> int:
    if signals == 0:
        return 0

    return SIGNAL_EXIT_BASE | signals


TOLERATED_CODES = tuple(exit_code(signals) for signals in range(2, EVERY_SIGNAL + 1, 2))


def finished_marker(name: str) -> Path:
    return Path(f".{name}-finished")


def signal_record(name: str) -> Path:
    return Path(f".{name}-signal")


def recorded_signals() -> list[Path]:
    return sorted(Path().glob(".*-signal"))

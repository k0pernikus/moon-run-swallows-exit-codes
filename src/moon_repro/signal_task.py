import sys
import time
from typing import Literal

import rich_click as click

from moon_repro.signals import SIGNAL_EXIT_BASE, exit_code, finished_marker, signal_record


@click.command(
    help="""Sleep SECONDS, write .NAME-finished, then either exit 64 | SIGNAL (mode exit) or record SIGNAL in \
.NAME-signal and exit 0 (mode record)."""
)
@click.argument("mode", type=click.Choice(["exit", "record"]))
@click.argument("name")
@click.argument("signal", type=int)
@click.argument("seconds", type=float)
def cli(mode: Literal["exit", "record"], name: str, signal: int, seconds: float) -> None:
    time.sleep(seconds)
    finished_marker(name).touch()
    if mode == "record":
        record = signal_record(name)
        record.write_text(f"{signal}\n", encoding="utf-8")
        click.echo(f"{name} finished after {seconds:g}s, recorded signal {signal} in {record}", err=True)
        sys.exit(0)

    code = exit_code(signal)
    click.echo(f"{name} finished after {seconds:g}s, exiting {SIGNAL_EXIT_BASE} | {signal} = {code}", err=True)
    sys.exit(code)

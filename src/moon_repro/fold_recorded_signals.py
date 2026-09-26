import sys
from functools import reduce
from operator import or_

import rich_click as click

from moon_repro.signals import exit_code, recorded_signals


@click.command(
    help="""The workaround's gate, run after moon: exit 64 | the OR of every recorded .NAME-signal, or 0 when no bit \
is set, and remove the records."""
)
def cli() -> None:
    records = recorded_signals()
    signals = reduce(or_, (int(record.read_text(encoding="utf-8")) for record in records), 0)
    for record in records:
        record.unlink()
    code = exit_code(signals)
    click.echo(f"fold-recorded-signals: {len(records)} recorded signal(s), OR = {signals}, exiting {code}", err=True)
    sys.exit(code)

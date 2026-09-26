import sys
from functools import reduce
from operator import or_

import rich_click as click

from moon_repro.signals import as_bits, recorded_signals


@click.command(
    help="""The workaround's gate, run after moon: exit the OR of every recorded .NAME-signal, \
0 when none is recorded, and remove the records."""
)
def cli() -> None:
    records = recorded_signals()
    code = reduce(or_, (int(record.read_text(encoding="utf-8")) for record in records), 0)
    for record in records:
        record.unlink()
    click.echo(
        f"fold-recorded-signals: {len(records)} recorded signal(s), exiting their OR {code} ({as_bits(code)})", err=True
    )
    sys.exit(code)

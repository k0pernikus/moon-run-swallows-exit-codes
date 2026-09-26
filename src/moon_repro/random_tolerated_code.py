import random
import sys

import rich_click as click

from moon_repro.signals import TOLERATED_CODES


@click.command(help="Exit a random tolerated code: 64 | a non-empty combination of the signal bits 2, 4 and 8.")
def cli() -> None:
    code = random.choice(TOLERATED_CODES)
    click.echo(f"random-tolerated-code exiting with code {code}", err=True)
    sys.exit(code)

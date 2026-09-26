import random
import sys

import rich_click as click

from moon_repro.signals import TOLERATED_CODES, as_bits


@click.command(help="Exit a random tolerated code: an OR of the signal bits 2, 4 and 8, one of the even codes 2 to 14.")
def cli() -> None:
    code = random.choice(TOLERATED_CODES)
    click.echo(f"random-tolerated-code exiting with code {code} ({as_bits(code)})", err=True)
    sys.exit(code)
